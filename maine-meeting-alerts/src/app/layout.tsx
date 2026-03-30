import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "Maine Meeting Alerts",
  description: "Monitor Maine public meetings, transcripts, and topic alerts — BDN Newsroom",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className="h-full antialiased"
    >
      <body className="min-h-full flex flex-col bg-zinc-50 dark:bg-zinc-950">
        <header className="border-b border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-900">
          <nav className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
            <Link href="/" className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">
              Maine Meeting Alerts
            </Link>
            <div className="flex gap-6 text-sm font-medium text-zinc-600 dark:text-zinc-400">
              <Link href="/meetings" className="hover:text-zinc-900 dark:hover:text-zinc-100">
                Meetings
              </Link>
              <Link href="/meetings/new" className="hover:text-zinc-900 dark:hover:text-zinc-100">
                Submit Meeting
              </Link>
              <Link href="/alerts" className="hover:text-zinc-900 dark:hover:text-zinc-100">
                My Alerts
              </Link>
            </div>
          </nav>
        </header>
        <main className="mx-auto w-full max-w-5xl flex-1 px-6 py-8">
          {children}
        </main>
        <footer className="border-t border-zinc-200 bg-white py-4 text-center text-xs text-zinc-500 dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-500">
          Maine Meeting Alerts — BDN Newsroom
        </footer>
      </body>
    </html>
  );
}
