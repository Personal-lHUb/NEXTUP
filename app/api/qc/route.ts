import { NextResponse } from "next/server";
import { z } from "zod";
import { USE_MOCK_DATA, QC_AUTO_APPROVE_HOURS } from "@/lib/constants";
import { getShippingProvider } from "@/lib/services/shipping";

const schema = z.object({
  projectId: z.string(),
  decision: z.enum(["approve", "reject"]),
});

// Client decision on the maker's QC photos. Approval triggers label generation.
export async function POST(req: Request) {
  const parsed = schema.safeParse(await req.json());
  if (!parsed.success) {
    return NextResponse.json({ error: parsed.error.flatten() }, { status: 400 });
  }
  const { projectId, decision } = parsed.data;

  if (decision === "reject") {
    if (!USE_MOCK_DATA) {
      const { prisma } = await import("@/lib/prisma");
      await prisma.project.update({
        where: { id: projectId },
        data: { qcStatus: "REJECTED", status: "PRINTING" },
      });
    }
    return NextResponse.json({ ok: true, qcStatus: "REJECTED" });
  }

  const shipping = getShippingProvider();
  const label = await shipping.createLabel(
    { name: "Maker", line1: "Via Roma 1", city: "Milano", postalCode: "20100", country: "IT" },
    { name: "Cliente", line1: "Via Verdi 2", city: "Roma", postalCode: "00100", country: "IT" },
    { weightG: 250, lengthMm: 200, widthMm: 150, heightMm: 100 },
  );

  if (!USE_MOCK_DATA) {
    const { prisma } = await import("@/lib/prisma");
    await prisma.project.update({
      where: { id: projectId },
      data: { qcStatus: "APPROVED", status: "SHIPPING" },
    });
    const order = await prisma.order.findUnique({ where: { projectId } });
    if (order) {
      await prisma.shippingLabel.upsert({
        where: { orderId: order.id },
        create: { orderId: order.id, ...label },
        update: { ...label },
      });
    }
  }

  return NextResponse.json({ ok: true, qcStatus: "APPROVED", label });
}

// Silent-consent sweep: auto-approve QC photos past the deadline.
// Intended to be triggered by a scheduled job (cron / queue).
export async function GET() {
  if (USE_MOCK_DATA) {
    return NextResponse.json({ ok: true, mock: true, autoApproveHours: QC_AUTO_APPROVE_HOURS, swept: 0 });
  }

  const { prisma } = await import("@/lib/prisma");
  const due = await prisma.project.findMany({
    where: { status: "QC_PENDING", qcStatus: "AWAITING_APPROVAL", qcDueAt: { lte: new Date() } },
    select: { id: true },
  });

  for (const p of due) {
    await prisma.project.update({
      where: { id: p.id },
      data: { qcStatus: "AUTO_APPROVED", status: "SHIPPING" },
    });
  }

  return NextResponse.json({ ok: true, swept: due.length });
}
