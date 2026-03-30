import { NextResponse } from "next/server";
import { prisma } from "@/lib/db";

export async function PATCH(
  request: Request,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params;
  const body = await request.json();

  const alertRule = await prisma.alertRule.update({
    where: { id },
    data: {
      ...(body.topicDescription !== undefined && { topicDescription: body.topicDescription }),
      ...(body.keywords !== undefined && { keywords: body.keywords }),
      ...(body.committeeFilter !== undefined && { committeeFilter: body.committeeFilter }),
      ...(body.isActive !== undefined && { isActive: body.isActive }),
    },
  });

  return NextResponse.json(alertRule);
}

export async function DELETE(
  _request: Request,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params;

  await prisma.alertRule.delete({ where: { id } });

  return NextResponse.json({ ok: true });
}
