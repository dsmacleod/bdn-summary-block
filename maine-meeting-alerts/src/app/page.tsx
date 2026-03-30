import Link from "next/link";
import { prisma } from "@/lib/db";

export const dynamic = "force-dynamic";

export default async function DashboardPage() {
  const recentMeetings = await prisma.meeting.findMany({
    orderBy: { createdAt: "desc" },
    take: 5,
    select: {
      id: true,
      title: true,
      committee: true,
      status: true,
      meetingDate: true,
      createdAt: true,
    },
  });

  const stats = {
    totalMeetings: await prisma.meeting.count(),
    completed: await prisma.meeting.count({ where: { status: "completed" } }),
    activeAlerts: await prisma.alertRule.count({ where: { isActive: true } }),
    notificationsSent: await prisma.notification.count({ where: { deliveredAt: { not: null } } }),
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-zinc-900 dark:text-zinc-100">Dashboard</h1>
        <p className="mt-1 text-sm text-zinc-500">
          Monitor Maine public meetings, transcripts, and topic alerts.
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        {[
          { label: "Total Meetings", value: stats.totalMeetings },
          { label: "Transcribed", value: stats.completed },
          { label: "Active Alerts", value: stats.activeAlerts },
          { label: "Notifications Sent", value: stats.notificationsSent },
        ].map((stat) => (
          <div
            key={stat.label}
            className="rounded-lg border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900"
          >
            <p className="text-sm text-zinc-500">{stat.label}</p>
            <p className="mt-1 text-2xl font-semibold text-zinc-900 dark:text-zinc-100">
              {stat.value}
            </p>
          </div>
        ))}
      </div>

      {/* Recent Meetings */}
      <div>
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">
            Recent Meetings
          </h2>
          <Link
            href="/meetings/new"
            className="rounded-md bg-blue-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-blue-700"
          >
            Submit Meeting
          </Link>
        </div>
        <div className="mt-4 overflow-hidden rounded-lg border border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-900">
          {recentMeetings.length === 0 ? (
            <p className="p-6 text-center text-sm text-zinc-500">
              No meetings yet.{" "}
              <Link href="/meetings/new" className="text-blue-600 hover:underline">
                Submit one
              </Link>{" "}
              to get started.
            </p>
          ) : (
            <ul className="divide-y divide-zinc-200 dark:divide-zinc-800">
              {recentMeetings.map((meeting) => (
                <li key={meeting.id}>
                  <Link
                    href={`/meetings/${meeting.id}`}
                    className="flex items-center justify-between px-4 py-3 hover:bg-zinc-50 dark:hover:bg-zinc-800/50"
                  >
                    <div>
                      <p className="font-medium text-zinc-900 dark:text-zinc-100">
                        {meeting.title}
                      </p>
                      {meeting.committee && (
                        <p className="text-sm text-zinc-500">{meeting.committee}</p>
                      )}
                    </div>
                    <StatusBadge status={meeting.status} />
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </div>
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
