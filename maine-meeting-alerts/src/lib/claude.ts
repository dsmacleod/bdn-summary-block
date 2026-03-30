import Anthropic from "@anthropic-ai/sdk";

const anthropic = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });

export interface TopicMatch {
  topic: string;
  relevantQuote: string;
  confidence: "high" | "medium" | "low";
}

/**
 * Check whether a transcript section discusses any of the given topics.
 * Uses Claude for semantic matching — catches topics even without exact keywords.
 */
export async function matchTopics(
  transcriptText: string,
  topics: { id: string; description: string; keywords: string[] }[],
): Promise<TopicMatch[]> {
  const topicList = topics
    .map((t, i) => `${i + 1}. "${t.description}"${t.keywords.length > 0 ? ` (related keywords: ${t.keywords.join(", ")})` : ""}`)
    .join("\n");

  const response = await anthropic.messages.create({
    model: "claude-sonnet-4-20250514",
    max_tokens: 1024,
    messages: [
      {
        role: "user",
        content: `You are analyzing a transcript from a Maine public meeting. Determine if the following transcript section discusses any of these topics:

${topicList}

Transcript section:
"""
${transcriptText}
"""

For each topic that IS discussed in this transcript, respond with a JSON array of objects with these fields:
- "topic": the topic description (exactly as listed above)
- "relevantQuote": a direct quote from the transcript (max 200 chars) that demonstrates the topic is being discussed
- "confidence": "high", "medium", or "low"

If no topics are discussed, respond with an empty array: []

Respond ONLY with the JSON array, no other text.`,
      },
    ],
  });

  const text = response.content[0].type === "text" ? response.content[0].text : "";

  try {
    const matches: TopicMatch[] = JSON.parse(text.trim());
    return matches.filter((m) => m.confidence === "high" || m.confidence === "medium");
  } catch {
    console.error("Failed to parse Claude response:", text);
    return [];
  }
}

/**
 * Generate a structured meeting summary from a full transcript.
 */
export async function generateMeetingSummary(transcriptText: string): Promise<string> {
  const response = await anthropic.messages.create({
    model: "claude-sonnet-4-20250514",
    max_tokens: 4096,
    messages: [
      {
        role: "user",
        content: `Summarize this Maine public meeting transcript in a structured format. Include:

1. **Meeting Overview**: A 2-3 sentence summary
2. **Agenda Items Discussed**: List each topic/agenda item with a brief summary
3. **Key Decisions & Votes**: Any motions, votes, or decisions made
4. **Action Items**: Any tasks assigned or next steps mentioned
5. **Notable Speakers & Positions**: Key participants and their stated positions

Transcript:
"""
${transcriptText.slice(0, 100000)}
"""

Provide the summary in markdown format.`,
      },
    ],
  });

  return response.content[0].type === "text" ? response.content[0].text : "";
}
