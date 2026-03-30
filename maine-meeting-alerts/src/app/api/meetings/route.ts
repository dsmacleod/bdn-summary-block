import { NextResponse } from "next/server";
import { prisma } from "@/lib/db";
import { transcriptionQueue } from "@/lib/queue";

export async function GET() {
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
    },
  });

  return NextResponse.json(meetings);
}

export async function POST(request: Request) {
  const body = await request.json();
  const { title, streamUrl, committee, meetingDate } = body;

  if (!title || !streamUrl) {
    return NextResponse.json(
      { error: "title and streamUrl are required" },
      { status: 400 },
    );
  }

  // Detect platform from URL
  let platform = "unknown";
  if (streamUrl.includes("youtube.com") || streamUrl.includes("youtu.be")) {
    platform = "youtube";
  } else if (streamUrl.includes("vimeo.com")) {
    platform = "vimeo";
  }

  const meeting = await prisma.meeting.create({
    data: {
      title,
      streamUrl,
      platform,
      committee: committee || null,
      meetingDate: meetingDate ? new Date(meetingDate) : null,
    },
  });

  // Queue transcription job
  await transcriptionQueue.add("transcribe", { meetingId: meeting.id });

  return NextResponse.json(meeting, { status: 201 });
}
