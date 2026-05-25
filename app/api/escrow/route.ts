import { NextResponse } from "next/server";
import { z } from "zod";
import { USE_MOCK_DATA } from "@/lib/constants";
import { computeOrderBreakdown } from "@/lib/money";
import { getEscrowProvider } from "@/lib/services/escrow";

const schema = z.object({
  orderId: z.string(),
  action: z.enum(["release", "refund"]),
});

// Releases held funds to designer + maker, or refunds the client.
export async function POST(req: Request) {
  const parsed = schema.safeParse(await req.json());
  if (!parsed.success) {
    return NextResponse.json({ error: parsed.error.flatten() }, { status: 400 });
  }
  const { orderId, action } = parsed.data;
  const escrow = getEscrowProvider();

  if (USE_MOCK_DATA) {
    if (action === "refund") {
      const r = await escrow.refund(orderId, `mock_pi_${orderId}`);
      return NextResponse.json({ ok: true, mock: true, ...r });
    }
    const demo = computeOrderBreakdown({ designPrice: 20, printPrice: 25, shippingCarrierCost: 7.5 });
    const r = await escrow.release(orderId, demo, { designerAccountId: null, makerAccountId: null }, "EUR");
    return NextResponse.json({ ok: true, mock: true, ...r });
  }

  const { prisma } = await import("@/lib/prisma");
  const order = await prisma.order.findUniqueOrThrow({
    where: { id: orderId },
    include: { project: { include: { designer: true, maker: true } } },
  });

  if (action === "refund") {
    const r = await escrow.refund(orderId, order.stripePaymentIntentId ?? "");
    await prisma.order.update({ where: { id: orderId }, data: { paymentStatus: "REFUNDED" } });
    return NextResponse.json({ ok: true, ...r });
  }

  const breakdown = computeOrderBreakdown({
    designPrice: Number(order.project.designPrice ?? 0),
    printPrice: Number(order.project.printPrice ?? 0),
    shippingCarrierCost: Number(order.shippingCost),
    takeRateBps: order.takeRateBps,
  });

  const result = await escrow.release(
    orderId,
    breakdown,
    {
      designerAccountId: order.project.designer?.stripeAccountId ?? null,
      makerAccountId: order.project.maker?.stripeAccountId ?? null,
    },
    order.currency,
  );

  await prisma.order.update({ where: { id: orderId }, data: { paymentStatus: "RELEASED" } });
  return NextResponse.json({ ok: true, ...result });
}
