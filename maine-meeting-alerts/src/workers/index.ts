/**
 * Worker entry point. Run this separately from the Next.js app:
 *   npx tsx src/workers/index.ts
 */
import { startTranscriptionWorker } from "./transcription";
import { startAlertMatcherWorker } from "./alert-matcher";
import { startSummarizerWorker } from "./summarizer";

console.log("Starting Maine Meeting Alert workers...");

const transcriptionWorker = startTranscriptionWorker();
const alertWorker = startAlertMatcherWorker();
const summaryWorker = startSummarizerWorker();

console.log("All workers started. Waiting for jobs...");

// Graceful shutdown
async function shutdown() {
  console.log("Shutting down workers...");
  await Promise.all([
    transcriptionWorker.close(),
    alertWorker.close(),
    summaryWorker.close(),
  ]);
  process.exit(0);
}

process.on("SIGINT", shutdown);
process.on("SIGTERM", shutdown);
