import Link from "next/link";
import { prisma } from "@/lib/db";

export const dynamic = "force-dynamic";

export default async function MeetingsPage() {
  const meetings = await prisma.meeting.findMany({
    orderBy: { createdAt: "desc" },
    select: {
      id: true,
      title: true,
      committee: true,
      platform: true,
      status: true,
      meetingDate: true,
      createdAt: true,
      _count: { select: { segments: true, notifications: true } },
    },
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-zinc-900 dark:text-zinc-100">Meetings</h1>
        <Link
          href="/meetings/new"
          className="rounded-md bg-blue-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-blue-700"
        >
          Submit Meeting
        </Link>
      </div>

      <div className="overflow-hidden rounded-lg border border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-900">
        {meetings.length === 0 ? (
          <p className="p-6 text-center text-sm text-zinc-500">No meetings yet.</p>
        ) : (
          <table className="w-full text-left text-sm">
            <thead className="border-b border-zinc-200 bg-zinc-50 text-xs uppercase text-zinc-500 dark:border-zinc-800 dark:bg-zinc-800/50">
              <tr>
                <th className="px-4 py-3">Title</th>
                <th className="px-4 py-3">Committee</th>
                <th className="px-4 py-3">Platform</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Segments</th>
                <th className="px-4 py-3">Date</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-200 dark:divide-zinc-800">
              {meetings.map((meeting) => (
                <tr key={meeting.id} className="hover:bg-zinc-50 dark:hover:bg-zinc-800/50">
                  <td className="px-4 py-3">
                    <Link
                      href={`/meetings/${meeting.id}`}
                      className="font-medium text-blue-600 hover:underline"
                    >
                      {meeting.title}
                    </Link>
                  </td>
                  <td className="px-4 py-3 text-zinc-500">{meeting.committee || "—"}</td>
                  <td className="px-4 py-3 text-zinc-500">{meeting.platform}</td>
                  <td className="px-4 py-3">
                    <StatusBadge status={meeting.status} />
                  </td>
                  <td className="px-4 py-3 text-zinc-500">{meeting._count.segments}</td>
                  <td className="px-4 py-3 text-zinc-500">
                    {meeting.meetingDate
                      ? new Date(meeting.meetingDate).toLocaleDateString()
                      : new Date(meeting.createdAt).toLocaleDateString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
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
