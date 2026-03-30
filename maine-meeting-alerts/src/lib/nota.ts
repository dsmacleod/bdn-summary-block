/**
 * Nota API client for key-point summarization.
 * Adapted from the bdn-summary-block WordPress plugin pattern.
 */

interface NotaKeyPoint {
  text: string;
}

/**
 * Generate key-point bullets from a transcript using Nota's API.
 */
export async function generateKeyPoints(text: string): Promise<string[]> {
  const apiUrl = process.env.NOTA_API_URL;
  const apiKey = process.env.NOTA_API_KEY;

  if (!apiUrl || !apiKey) {
    console.warn("Nota API credentials not configured, skipping key points");
    return [];
  }

  const response = await fetch(`${apiUrl}/wordpress/v1/sum/key-points`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "nota-subscription-key": apiKey,
    },
    body: JSON.stringify({
      content: text.slice(0, 60000),
      contentInputSource: {
        cmsProvider: "maine-meeting-alerts",
      },
    }),
  });

  if (!response.ok) {
    console.error(`Nota API error: ${response.status} ${response.statusText}`);
    return [];
  }

  const data = await response.json();

  // Handle flexible response shapes (same as bdn-summary-block plugin)
  const points: string[] = [];
  const candidates = data.keyPoints ?? data.result?.keyPoints ?? data.data ?? data.key_points ?? [];

  for (const item of candidates) {
    if (typeof item === "string") {
      points.push(item);
    } else if (item && typeof item === "object" && "text" in item) {
      points.push((item as NotaKeyPoint).text);
    }
  }

  return points;
}
