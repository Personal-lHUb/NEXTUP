import { NextResponse } from "next/server";
import { z } from "zod";
import { getShippingProvider } from "@/lib/services/shipping";

const addressSchema = z.object({
  name: z.string(),
  line1: z.string(),
  city: z.string(),
  postalCode: z.string(),
  country: z.string().length(2),
});

const schema = z.object({
  from: addressSchema,
  to: addressSchema,
  parcel: z.object({
    weightG: z.number().positive(),
    lengthMm: z.number().positive(),
    widthMm: z.number().positive(),
    heightMm: z.number().positive(),
  }),
  quoteOnly: z.boolean().default(false),
});

// Quotes a shipment or generates a ready-to-print PDF label.
export async function POST(req: Request) {
  const parsed = schema.safeParse(await req.json());
  if (!parsed.success) {
    return NextResponse.json({ error: parsed.error.flatten() }, { status: 400 });
  }
  const { from, to, parcel, quoteOnly } = parsed.data;
  const shipping = getShippingProvider();

  if (quoteOnly) {
    const quote = await shipping.quote(from, to, parcel);
    return NextResponse.json({ ok: true, quote });
  }

  const label = await shipping.createLabel(from, to, parcel);
  return NextResponse.json({ ok: true, label });
}
