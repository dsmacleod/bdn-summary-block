import { NextResponse } from "next/server";
import { prisma } from "@/lib/db";

export async function GET() {
  const users = await prisma.user.findMany({
    orderBy: { createdAt: "desc" },
    include: { _count: { select: { alertRules: true } } },
  });

  return NextResponse.json(users);
}

export async function POST(request: Request) {
  const body = await request.json();
  const { email, name } = body;

  if (!email) {
    return NextResponse.json({ error: "email is required" }, { status: 400 });
  }

  const user = await prisma.user.upsert({
    where: { email },
    update: { name: name || undefined },
    create: { email, name: name || null },
  });

  return NextResponse.json(user, { status: 201 });
}
