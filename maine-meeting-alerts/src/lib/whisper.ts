import OpenAI from "openai";
import { createReadStream } from "fs";

const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

export interface WhisperSegment {
  text: string;
  start: number;
  end: number;
}

export interface WhisperResult {
  text: string;
  segments: WhisperSegment[];
}

/**
 * Transcribe an audio file using OpenAI Whisper API.
 * Returns the full text and timestamped segments.
 */
export async function transcribeAudio(filePath: string): Promise<WhisperResult> {
  const response = await openai.audio.transcriptions.create({
    file: createReadStream(filePath),
    model: "whisper-1",
    response_format: "verbose_json",
    timestamp_granularities: ["segment"],
  });

  const segments: WhisperSegment[] = (response.segments ?? []).map((seg) => ({
    text: seg.text.trim(),
    start: seg.start,
    end: seg.end,
  }));

  return {
    text: response.text,
    segments,
  };
}
