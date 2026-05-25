import { NextResponse } from "next/server";
import { z } from "zod";
import { USE_MOCK_DATA } from "@/lib/constants";
import { computeOrderBreakdown } from "@/lib/money";
import { getEscrowProvider } from "@/lib/services/escrow";
import { getClientProjects } from "@/lib/repositories/projects";

export async function GET() {
  const projects = await getClientProjects();
  return NextResponse.json({ projects });
}

const createSchema = z.object({
  clientId: z.string().optional(),
  title: z.string().min(3),
  description: z.string().min(1),
  category: z.string().min(1),
  designerId: z.string().optional(),
  designPrice: z.number().nonnegative(),
  printPrice: z.number().nonnegative(),
  shippingCarrierCost: z.number().nonnegative().default(7.5),
  material: z.string().optional(),
  requiredX: z.number().positive().optional(),
  requiredY: z.number().positive().optional(),
  requiredZ: z.number().positive().optional(),
});

// Creates a project + order and holds the full amount in escrow.
export async function POST(req: Request) {
  const parsed = createSchema.safeParse(await req.json());
  if (!parsed.success) {
    return NextResponse.json({ error: parsed.error.flatten() }, { status: 400 });
  }
  const input = parsed.data;

  const breakdown = computeOrderBreakdown({
    designPrice: input.designPrice,
    printPrice: input.printPrice,
    shippingCarrierCost: input.shippingCarrierCost,
  });

  if (USE_MOCK_DATA) {
    const escrow = getEscrowProvider();
    const hold = await escrow.hold(`mock_order_${Date.now()}`, breakdown, "EUR");
    return NextResponse.json({ ok: true, mock: true, breakdown, escrow: hold }, { status: 201 });
  }

  const { prisma } = await import("@/lib/prisma");
  const project = await prisma.project.create({
    data: {
      title: input.title,
      description: input.description,
      category: input.category,
      clientId: input.clientId!,
      designerId: input.designerId,
      designPrice: input.designPrice,
      printPrice: input.printPrice,
      material: input.material as never,
      requiredX: input.requiredX,
      requiredY: input.requiredY,
      requiredZ: input.requiredZ,
      status: "MODELING",
    },
  });

  const order = await prisma.order.create({
    data: {
      projectId: project.id,
      itemsTotal: breakdown.itemsTotal,
      shippingCost: breakdown.shippingCost,
      platformFee: breakdown.platformFee,
      designerPayout: breakdown.designerPayout,
      makerPayout: breakdown.makerPayout,
      takeRateBps: breakdown.takeRateBps,
    },
  });

  const escrow = getEscrowProvider();
  const hold = await escrow.hold(order.id, breakdown, "EUR");
  await prisma.order.update({
    where: { id: order.id },
    data: { paymentStatus: "HELD", stripePaymentIntentId: hold.paymentIntentId },
  });

  return NextResponse.json({ ok: true, projectId: project.id, breakdown }, { status: 201 });
}
