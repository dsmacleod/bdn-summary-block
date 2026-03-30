import { execFile } from "child_process";
import { promisify } from "util";
import { stat, unlink, readdir } from "fs/promises";
import { join } from "path";
import { tmpdir } from "os";
import { prisma } from "@/lib/db";
import { transcribeAudio } from "@/lib/whisper";
import { createWorker, alertQueue, summaryQueue } from "@/lib/queue";

const execFileAsync = promisify(execFile);

const WHISPER_MAX_SIZE = 24 * 1024 * 1024; // 24MB to stay under 25MB limit

interface TranscriptionJob {
  meetingId: string;
}

/**
 * Download audio from a YouTube/Vimeo URL using yt-dlp.
 * Returns the path to the downloaded audio file.
 */
async function downloadAudio(url: string, outputDir: string): Promise<string> {
  const outputPath = join(outputDir, "meeting-audio.mp3");

  await execFileAsync("yt-dlp", [
    "--extract-audio",
    "--audio-format", "mp3",
    "--audio-quality", "4", // medium quality, smaller file
    "--output", outputPath,
    "--no-playlist",
    url,
  ], { timeout: 600_000 }); // 10 minute timeout

  return outputPath;
}

/**
 * Split a large audio file into chunks under the Whisper size limit.
 * Uses ffmpeg to split by duration.
 */
async function splitAudioIfNeeded(filePath: string, outputDir: string): Promise<string[]> {
  const fileStat = await stat(filePath);

  if (fileStat.size <= WHISPER_MAX_SIZE) {
    return [filePath];
  }

  // Estimate chunk duration based on file size
  // MP3 at quality 4 is roughly 128kbps = 16KB/s
  const totalDurationEstimate = fileStat.size / (16 * 1024);
  const numChunks = Math.ceil(fileStat.size / WHISPER_MAX_SIZE);
  const chunkDuration = Math.ceil(totalDurationEstimate / numChunks);

  await execFileAsync("ffmpeg", [
    "-i", filePath,
    "-f", "segment",
    "-segment_time", String(chunkDuration),
    "-c", "copy",
    join(outputDir, "chunk-%03d.mp3"),
  ], { timeout: 300_000 });

  const files = await readdir(outputDir);
  return files
    .filter((f) => f.startsWith("chunk-") && f.endsWith(".mp3"))
    .sort()
    .map((f) => join(outputDir, f));
}

/**
 * Clean up temporary files.
 */
async function cleanup(dir: string) {
  try {
    const files = await readdir(dir);
    await Promise.all(files.map((f) => unlink(join(dir, f)).catch(() => {})));
  } catch {
    // Ignore cleanup errors
  }
}

/**
 * Main transcription worker processor.
 */
const transcriptionProcessor = async (job: { data: TranscriptionJob }) => {
  const { meetingId } = job.data;

  const meeting = await prisma.meeting.findUnique({ where: { id: meetingId } });
  if (!meeting) throw new Error(`Meeting ${meetingId} not found`);

  await prisma.meeting.update({
    where: { id: meetingId },
    data: { status: "transcribing" },
  });

  const workDir = join(tmpdir(), `meeting-${meetingId}`);
  await execFileAsync("mkdir", ["-p", workDir]);

  try {
    // Step 1: Download audio
    console.log(`Downloading audio for meeting ${meetingId}...`);
    const audioPath = await downloadAudio(meeting.streamUrl, workDir);

    // Step 2: Split if needed
    console.log(`Splitting audio if needed...`);
    const chunks = await splitAudioIfNeeded(audioPath, workDir);

    // Step 3: Transcribe each chunk
    let segmentIndex = 0;
    let timeOffset = 0;

    for (const chunkPath of chunks) {
      console.log(`Transcribing chunk ${chunkPath}...`);
      const result = await transcribeAudio(chunkPath);

      // Save segments to database
      const segmentsToCreate = result.segments.map((seg) => ({
        meetingId,
        text: seg.text,
        startTime: seg.start + timeOffset,
        endTime: seg.end + timeOffset,
        segmentIndex: segmentIndex++,
      }));

      if (segmentsToCreate.length > 0) {
        await prisma.transcriptSegment.createMany({ data: segmentsToCreate });
        // Update time offset for next chunk
        const lastSeg = result.segments[result.segments.length - 1];
        timeOffset += lastSeg.end;
      }
    }

    // Step 4: Update status and queue follow-up jobs
    await prisma.meeting.update({
      where: { id: meetingId },
      data: { status: "analyzing" },
    });

    await alertQueue.add("match-topics", { meetingId });
    await summaryQueue.add("summarize", { meetingId });

    console.log(`Transcription complete for meeting ${meetingId}: ${segmentIndex} segments`);
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    await prisma.meeting.update({
      where: { id: meetingId },
      data: { status: "failed", errorMessage: message },
    });
    throw error;
  } finally {
    await cleanup(workDir);
  }
};

export function startTranscriptionWorker() {
  return createWorker<TranscriptionJob>("transcription", transcriptionProcessor);
}
