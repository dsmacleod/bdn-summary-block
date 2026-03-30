import { NextResponse } from "next/server";
import { prisma } from "@/lib/db";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const userId = searchParams.get("userId");

  const alertRules = await prisma.alertRule.findMany({
    where: userId ? { userId } : {},
    include: {
      user: { select: { email: true, name: true } },
      _count: { select: { notifications: true } },
    },
    orderBy: { createdAt: "desc" },
  });

  return NextResponse.json(alertRules);
}

export async function POST(request: Request) {
  const body = await request.json();
  const { userId, topicDescription, keywords, committeeFilter } = body;

  if (!userId || !topicDescription) {
    return NextResponse.json(
      { error: "userId and topicDescription are required" },
      { status: 400 },
    );
  }

  // Ensure user exists
  const user = await prisma.user.findUnique({ where: { id: userId } });
  if (!user) {
    return NextResponse.json({ error: "User not found" }, { status: 404 });
  }

  const alertRule = await prisma.alertRule.create({
    data: {
      userId,
      topicDescription,
      keywords: keywords || [],
      committeeFilter: committeeFilter || null,
    },
  });

  return NextResponse.json(alertRule, { status: 201 });
}
