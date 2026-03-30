"use client";

import { useState, useEffect, useCallback } from "react";

interface AlertRule {
  id: string;
  topicDescription: string;
  keywords: string[];
  committeeFilter: string | null;
  isActive: boolean;
  createdAt: string;
  _count: { notifications: number };
  user: { email: string; name: string | null };
}

interface User {
  id: string;
  email: string;
  name: string | null;
}

export default function AlertsPage() {
  const [rules, setRules] = useState<AlertRule[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);

  const loadData = useCallback(async () => {
    const [rulesRes, usersRes] = await Promise.all([
      fetch("/api/alerts"),
      fetch("/api/users"),
    ]);
    setRules(await rulesRes.json());
    setUsers(await usersRes.json());
    setLoading(false);
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  async function handleCreateAlert(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);

    let userId = formData.get("userId") as string;

    // If no users exist, create one first
    if (!userId) {
      const email = formData.get("email") as string;
      const name = formData.get("name") as string;
      if (!email) return;

      const userRes = await fetch("/api/users", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, name }),
      });
      const user = await userRes.json();
      userId = user.id;
    }

    const keywordsStr = formData.get("keywords") as string;
    const keywords = keywordsStr
      ? keywordsStr.split(",").map((k) => k.trim()).filter(Boolean)
      : [];

    await fetch("/api/alerts", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        userId,
        topicDescription: formData.get("topicDescription"),
        keywords,
        committeeFilter: formData.get("committeeFilter") || null,
      }),
    });

    setShowForm(false);
    loadData();
  }

  async function toggleAlert(id: string, isActive: boolean) {
    await fetch(`/api/alerts/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ isActive: !isActive }),
    });
    loadData();
  }

  async function deleteAlert(id: string) {
    await fetch(`/api/alerts/${id}`, { method: "DELETE" });
    loadData();
  }

  if (loading) {
    return <p className="text-sm text-zinc-500">Loading...</p>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-zinc-900 dark:text-zinc-100">Topic Alerts</h1>
          <p className="mt-1 text-sm text-zinc-500">
            Get notified when specific topics come up in Maine public meetings.
          </p>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          className="rounded-md bg-blue-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-blue-700"
        >
          {showForm ? "Cancel" : "New Alert"}
        </button>
      </div>

      {/* Create Form */}
      {showForm && (
        <form
          onSubmit={handleCreateAlert}
          className="space-y-4 rounded-lg border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900"
        >
          {users.length === 0 ? (
            <>
              <div>
                <label htmlFor="email" className="block text-sm font-medium text-zinc-700 dark:text-zinc-300">
                  Your Email *
                </label>
                <input
                  id="email"
                  name="email"
                  type="email"
                  required
                  className="mt-1 block w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100"
                />
              </div>
              <div>
                <label htmlFor="name" className="block text-sm font-medium text-zinc-700 dark:text-zinc-300">
                  Your Name
                </label>
                <input
                  id="name"
                  name="name"
                  type="text"
                  className="mt-1 block w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100"
                />
              </div>
            </>
          ) : (
            <div>
              <label htmlFor="userId" className="block text-sm font-medium text-zinc-700 dark:text-zinc-300">
                User
              </label>
              <select
                id="userId"
                name="userId"
                className="mt-1 block w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100"
              >
                {users.map((u) => (
                  <option key={u.id} value={u.id}>
                    {u.name || u.email}
                  </option>
                ))}
              </select>
            </div>
          )}

          <div>
            <label htmlFor="topicDescription" className="block text-sm font-medium text-zinc-700 dark:text-zinc-300">
              Topic Description *
            </label>
            <input
              id="topicDescription"
              name="topicDescription"
              type="text"
              required
              placeholder='e.g. "school funding and education budget"'
              className="mt-1 block w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100"
            />
            <p className="mt-1 text-xs text-zinc-400">
              Describe the topic in natural language. Claude will match semantically, not just keywords.
            </p>
          </div>

          <div>
            <label htmlFor="keywords" className="block text-sm font-medium text-zinc-700 dark:text-zinc-300">
              Keywords (optional, comma-separated)
            </label>
            <input
              id="keywords"
              name="keywords"
              type="text"
              placeholder="e.g. education, budget, school board"
              className="mt-1 block w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100"
            />
          </div>

          <div>
            <label htmlFor="committeeFilter" className="block text-sm font-medium text-zinc-700 dark:text-zinc-300">
              Committee Filter (optional)
            </label>
            <input
              id="committeeFilter"
              name="committeeFilter"
              type="text"
              placeholder="e.g. Portland School Board"
              className="mt-1 block w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100"
            />
          </div>

          <button
            type="submit"
            className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
          >
            Create Alert
          </button>
        </form>
      )}

      {/* Alert Rules List */}
      <div className="overflow-hidden rounded-lg border border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-900">
        {rules.length === 0 ? (
          <p className="p-6 text-center text-sm text-zinc-500">
            No alert rules yet. Create one to get started.
          </p>
        ) : (
          <ul className="divide-y divide-zinc-200 dark:divide-zinc-800">
            {rules.map((rule) => (
              <li key={rule.id} className="flex items-center justify-between px-4 py-3">
                <div>
                  <p className="font-medium text-zinc-900 dark:text-zinc-100">
                    {rule.topicDescription}
                  </p>
                  <div className="mt-0.5 flex gap-3 text-xs text-zinc-500">
                    {rule.keywords.length > 0 && (
                      <span>Keywords: {rule.keywords.join(", ")}</span>
                    )}
                    {rule.committeeFilter && (
                      <span>Committee: {rule.committeeFilter}</span>
                    )}
                    <span>{rule._count.notifications} notifications sent</span>
                    <span>{rule.user.email}</span>
                  </div>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => toggleAlert(rule.id, rule.isActive)}
                    className={`rounded px-2 py-1 text-xs font-medium ${
                      rule.isActive
                        ? "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400"
                        : "bg-zinc-100 text-zinc-500 dark:bg-zinc-800 dark:text-zinc-500"
                    }`}
                  >
                    {rule.isActive ? "Active" : "Paused"}
                  </button>
                  <button
                    onClick={() => deleteAlert(rule.id)}
                    className="rounded px-2 py-1 text-xs font-medium text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20"
                  >
                    Delete
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
