import { NextResponse } from "next/server";
import { z } from "zod";
import { USE_MOCK_DATA } from "@/lib/constants";
import { getCurrentUser } from "@/lib/auth/guards";
import { getMakerPrinters } from "@/lib/repositories/printers";

export async function GET() {
  const printers = await getMakerPrinters();
  return NextResponse.json({ printers });
}

const addPrinterSchema = z.object({
  name: z.string().min(1),
  technology: z.enum(["FDM", "SLA", "DLP", "SLS", "MJF"]),
  buildX: z.number().positive(),
  buildY: z.number().positive(),
  buildZ: z.number().positive(),
  materials: z.array(z.string()).min(1),
});

// Adds a printer for the authenticated maker.
// (Starting a protected print lives at POST /api/print/start.)
export async function POST(req: Request) {
  const user = await getCurrentUser();
  if (!user) return NextResponse.json({ error: "Non autenticato" }, { status: 401 });
  if (!user.roles.includes("MAKER")) {
    return NextResponse.json({ error: "Ruolo non autorizzato" }, { status: 403 });
  }

  const parsed = addPrinterSchema.safeParse(await req.json());
  if (!parsed.success) {
    return NextResponse.json({ error: parsed.error.flatten() }, { status: 400 });
  }
  const body = parsed.data;

  if (USE_MOCK_DATA) {
    return NextResponse.json({ ok: true, mock: true, printer: { id: `ptr_${Date.now()}`, ...body } }, { status: 201 });
  }

  const { prisma } = await import("@/lib/prisma");
  const printer = await prisma.printer.create({
    data: {
      makerId: user.id,
      name: body.name,
      technology: body.technology,
      buildX: body.buildX,
      buildY: body.buildY,
      buildZ: body.buildZ,
      materials: body.materials as never,
    },
  });
  return NextResponse.json({ ok: true, printer }, { status: 201 });
}
