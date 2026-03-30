import { prisma } from "@/lib/db";
import { generateMeetingSummary } from "@/lib/claude";
import { generateKeyPoints } from "@/lib/nota";
import { createWorker } from "@/lib/queue";

interface SummarizationJob {
  meetingId: string;
}

const summarizationProcessor = async (job: { data: SummarizationJob }) => {
  const { meetingId } = job.data;

  const meeting = await prisma.meeting.findUnique({
    where: { id: meetingId },
    include: { segments: { orderBy: { segmentIndex: "asc" } } },
  });
  if (!meeting) throw new Error(`Meeting ${meetingId} not found`);

  const fullTranscript = meeting.segments.map((s) => s.text).join(" ");

  // Run Claude summary and Nota key points in parallel
  const [summary, keyPoints] = await Promise.all([
    generateMeetingSummary(fullTranscript),
    generateKeyPoints(fullTranscript),
  ]);

  await prisma.meeting.update({
    where: { id: meetingId },
    data: {
      summary,
      keyPoints: keyPoints.length > 0 ? keyPoints : undefined,
      status: "completed",
    },
  });

  console.log(`Summarization complete for meeting ${meetingId}`);
};

export function startSummarizerWorker() {
  return createWorker<SummarizationJob>("summarization", summarizationProcessor);
}
