import { Resend } from "resend";

const resend = new Resend(process.env.RESEND_API_KEY);

interface AlertEmailParams {
  to: string;
  userName: string;
  meetingTitle: string;
  matchedTopic: string;
  relevantQuote: string;
  meetingUrl: string;
}

export async function sendAlertEmail({
  to,
  userName,
  meetingTitle,
  matchedTopic,
  relevantQuote,
  meetingUrl,
}: AlertEmailParams): Promise<boolean> {
  try {
    await resend.emails.send({
      from: process.env.EMAIL_FROM || "Maine Meeting Alerts <alerts@meetings.example.com>",
      to,
      subject: `Meeting Alert: "${matchedTopic}" discussed in ${meetingTitle}`,
      html: `
        <div style="font-family: Georgia, serif; max-width: 600px; margin: 0 auto;">
          <h2 style="color: #1a1a1a;">Meeting Alert</h2>
          <p>Hi ${userName || "there"},</p>
          <p>Your alert topic <strong>"${matchedTopic}"</strong> was discussed in:</p>
          <div style="background: #f5f5f5; padding: 16px; border-left: 4px solid #2563eb; margin: 16px 0;">
            <strong>${meetingTitle}</strong>
          </div>
          <p><em>Relevant excerpt:</em></p>
          <blockquote style="border-left: 3px solid #ccc; padding-left: 12px; color: #444;">
            "${relevantQuote}"
          </blockquote>
          <p><a href="${meetingUrl}" style="color: #2563eb;">View full transcript &rarr;</a></p>
          <hr style="border: none; border-top: 1px solid #eee; margin: 24px 0;" />
          <p style="color: #888; font-size: 12px;">Maine Meeting Alerts — BDN Newsroom</p>
        </div>
      `,
    });
    return true;
  } catch (error) {
    console.error("Failed to send alert email:", error);
    return false;
  }
}
