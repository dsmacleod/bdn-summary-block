import { notFound } from "next/navigation";
import { prisma } from "@/lib/db";

export const dynamic = "force-dynamic";

function formatTime(seconds: number): string {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);
  if (h > 0) return `${h}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
  return `${m}:${String(s).padStart(2, "0")}`;
}

export default async function MeetingDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

  const meeting = await prisma.meeting.findUnique({
    where: { id },
    include: {
      segments: { orderBy: { segmentIndex: "asc" } },
      notifications: {
        include: { alertRule: true },
        orderBy: { createdAt: "desc" },
      },
    },
  });

  if (!meeting) notFound();

  const keyPoints = meeting.keyPoints as string[] | null;

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-bold text-zinc-900 dark:text-zinc-100">
            {meeting.title}
          </h1>
          <StatusBadge status={meeting.status} />
        </div>
        {meeting.committee && (
          <p className="mt-1 text-sm text-zinc-500">{meeting.committee}</p>
        )}
        <p className="mt-1 text-sm text-zinc-400">
          {meeting.meetingDate
            ? new Date(meeting.meetingDate).toLocaleDateString()
            : new Date(meeting.createdAt).toLocaleDateString()}
          {" · "}
          <a
            href={meeting.streamUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-600 hover:underline"
          >
            Original video
          </a>
        </p>
      </div>

      {/* Error */}
      {meeting.status === "failed" && meeting.errorMessage && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700 dark:border-red-900 dark:bg-red-900/20 dark:text-red-400">
          <strong>Error:</strong> {meeting.errorMessage}
        </div>
      )}

      {/* Topic Alerts */}
      {meeting.notifications.length > 0 && (
        <div>
          <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">
            Topic Alerts Triggered
          </h2>
          <div className="mt-3 space-y-2">
            {meeting.notifications.map((n) => (
              <div
                key={n.id}
                className="rounded-lg border border-amber-200 bg-amber-50 p-3 dark:border-amber-900 dark:bg-amber-900/20"
              >
                <p className="font-medium text-amber-800 dark:text-amber-400">
                  {n.matchedTopic}
                </p>
                {n.relevantQuote && (
                  <p className="mt-1 text-sm italic text-amber-700 dark:text-amber-500">
                    &ldquo;{n.relevantQuote}&rdquo;
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Summary */}
      {meeting.summary && (
        <div>
          <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">
            Meeting Summary
          </h2>
          <div className="prose prose-sm prose-zinc mt-3 max-w-none rounded-lg border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900 dark:prose-invert">
            {meeting.summary.split("\n").map((line, i) => (
              <p key={i}>{line}</p>
            ))}
          </div>
        </div>
      )}

      {/* Key Points (Nota) */}
      {keyPoints && keyPoints.length > 0 && (
        <div>
          <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">
            Key Points
          </h2>
          <ul className="mt-3 space-y-1.5">
            {keyPoints.map((point, i) => (
              <li
                key={i}
                className="flex items-start gap-2 text-sm text-zinc-700 dark:text-zinc-300"
              >
                <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-blue-500" />
                {point}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Transcript */}
      <div>
        <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">
          Transcript
          {meeting.segments.length > 0 && (
            <span className="ml-2 text-sm font-normal text-zinc-500">
              ({meeting.segments.length} segments)
            </span>
          )}
        </h2>

        {meeting.segments.length === 0 ? (
          <p className="mt-3 text-sm text-zinc-500">
            {meeting.status === "pending"
              ? "Transcription queued..."
              : meeting.status === "transcribing"
                ? "Transcription in progress..."
                : "No transcript available."}
          </p>
        ) : (
          <div className="mt-3 space-y-1 rounded-lg border border-zinc-200 bg-white p-4 font-mono text-sm dark:border-zinc-800 dark:bg-zinc-900">
            {meeting.segments.map((seg) => (
              <div key={seg.id} className="flex gap-3">
                <span className="shrink-0 text-xs text-zinc-400 tabular-nums">
                  {formatTime(seg.startTime)}
                </span>
                <span className="text-zinc-700 dark:text-zinc-300">{seg.text}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    pending: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400",
    transcribing: "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400",
    analyzing: "bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400",
    completed: "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400",
    failed: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400",
  };

  return (
    <span
      className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${colors[status] || "bg-zinc-100 text-zinc-800"}`}
    >
      {status}
    </span>
  );
}
