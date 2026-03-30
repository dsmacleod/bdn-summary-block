"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export default function NewMeetingPage() {
  const router = useRouter();
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);

    const formData = new FormData(e.currentTarget);

    const res = await fetch("/api/meetings", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        title: formData.get("title"),
        streamUrl: formData.get("streamUrl"),
        committee: formData.get("committee") || null,
        meetingDate: formData.get("meetingDate") || null,
      }),
    });

    if (!res.ok) {
      const data = await res.json();
      setError(data.error || "Failed to submit meeting");
      setSubmitting(false);
      return;
    }

    const meeting = await res.json();
    router.push(`/meetings/${meeting.id}`);
  }

  return (
    <div className="mx-auto max-w-xl space-y-6">
      <h1 className="text-2xl font-bold text-zinc-900 dark:text-zinc-100">Submit a Meeting</h1>
      <p className="text-sm text-zinc-500">
        Paste a YouTube or Vimeo URL of a Maine public meeting. The system will download the audio,
        transcribe it, and check it against your alert topics.
      </p>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="title" className="block text-sm font-medium text-zinc-700 dark:text-zinc-300">
            Meeting Title *
          </label>
          <input
            id="title"
            name="title"
            type="text"
            required
            placeholder="e.g. Portland City Council — March 2026"
            className="mt-1 block w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100"
          />
        </div>

        <div>
          <label htmlFor="streamUrl" className="block text-sm font-medium text-zinc-700 dark:text-zinc-300">
            Video URL *
          </label>
          <input
            id="streamUrl"
            name="streamUrl"
            type="url"
            required
            placeholder="https://www.youtube.com/watch?v=..."
            className="mt-1 block w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100"
          />
        </div>

        <div>
          <label htmlFor="committee" className="block text-sm font-medium text-zinc-700 dark:text-zinc-300">
            Committee / Body
          </label>
          <input
            id="committee"
            name="committee"
            type="text"
            placeholder="e.g. Portland City Council"
            className="mt-1 block w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100"
          />
        </div>

        <div>
          <label htmlFor="meetingDate" className="block text-sm font-medium text-zinc-700 dark:text-zinc-300">
            Meeting Date
          </label>
          <input
            id="meetingDate"
            name="meetingDate"
            type="date"
            className="mt-1 block w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100"
          />
        </div>

        {error && (
          <p className="text-sm text-red-600">{error}</p>
        )}

        <button
          type="submit"
          disabled={submitting}
          className="w-full rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
        >
          {submitting ? "Submitting..." : "Submit & Start Transcription"}
        </button>
      </form>
    </div>
  );
}
