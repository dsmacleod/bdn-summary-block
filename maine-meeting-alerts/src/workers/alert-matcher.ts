import { prisma } from "@/lib/db";
import { matchTopics } from "@/lib/claude";
import { sendAlertEmail } from "@/lib/email";
import { createWorker } from "@/lib/queue";

interface AlertMatchingJob {
  meetingId: string;
}

const CHUNK_SIZE = 3000; // characters per chunk sent to Claude

/**
 * Split transcript into overlapping chunks for topic matching.
 */
function chunkTranscript(segments: { text: string }[]): string[] {
  const fullText = segments.map((s) => s.text).join(" ");
  const chunks: string[] = [];

  for (let i = 0; i < fullText.length; i += CHUNK_SIZE - 500) {
    chunks.push(fullText.slice(i, i + CHUNK_SIZE));
  }

  return chunks;
}

const alertMatchingProcessor = async (job: { data: AlertMatchingJob }) => {
  const { meetingId } = job.data;

  const meeting = await prisma.meeting.findUnique({
    where: { id: meetingId },
    include: { segments: { orderBy: { segmentIndex: "asc" } } },
  });
  if (!meeting) throw new Error(`Meeting ${meetingId} not found`);

  // Get all active alert rules with their users
  const alertRules = await prisma.alertRule.findMany({
    where: {
      isActive: true,
      ...(meeting.committee
        ? {
            OR: [
              { committeeFilter: null },
              { committeeFilter: meeting.committee },
            ],
          }
        : {}),
    },
    include: { user: true },
  });

  if (alertRules.length === 0) {
    console.log(`No active alert rules for meeting ${meetingId}`);
    return;
  }

  const chunks = chunkTranscript(meeting.segments);
  const topics = alertRules.map((rule) => ({
    id: rule.id,
    description: rule.topicDescription,
    keywords: rule.keywords,
  }));

  // Track which topics we've already matched to avoid duplicate notifications
  const matchedTopics = new Set<string>();

  for (const chunk of chunks) {
    const matches = await matchTopics(chunk, topics);

    for (const match of matches) {
      // Find the corresponding alert rule
      const rule = alertRules.find((r) => r.topicDescription === match.topic);
      if (!rule || matchedTopics.has(`${rule.id}`)) continue;

      matchedTopics.add(`${rule.id}`);

      // Create notification record
      const notification = await prisma.notification.create({
        data: {
          userId: rule.userId,
          alertRuleId: rule.id,
          meetingId,
          matchedTopic: match.topic,
          relevantQuote: match.relevantQuote,
          channel: "email",
        },
      });

      // Send email
      const appUrl = process.env.NEXT_PUBLIC_APP_URL || "http://localhost:3000";
      const delivered = await sendAlertEmail({
        to: rule.user.email,
        userName: rule.user.name || "",
        meetingTitle: meeting.title,
        matchedTopic: match.topic,
        relevantQuote: match.relevantQuote,
        meetingUrl: `${appUrl}/meetings/${meetingId}`,
      });

      if (delivered) {
        await prisma.notification.update({
          where: { id: notification.id },
          data: { deliveredAt: new Date() },
        });
      }

      console.log(`Alert: "${match.topic}" matched for user ${rule.user.email} in meeting ${meetingId}`);
    }
  }

  console.log(`Alert matching complete for meeting ${meetingId}: ${matchedTopics.size} topics matched`);
};

export function startAlertMatcherWorker() {
  return createWorker<AlertMatchingJob>("alert-matching", alertMatchingProcessor);
}
