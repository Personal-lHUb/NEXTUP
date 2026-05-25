import { NextResponse } from "next/server";
import { z } from "zod";
import { USE_MOCK_DATA } from "@/lib/constants";
import { getMakerPrinters } from "@/lib/repositories/printers";
import { issueGcodeStreamToken } from "@/lib/services/file-protection";

export async function GET() {
  const printers = await getMakerPrinters();
  return NextResponse.json({ printers });
}

const addPrinterSchema = z.object({
  action: z.literal("add"),
  makerId: z.string().optional(),
  name: z.string().min(1),
  technology: z.enum(["FDM", "SLA", "DLP", "SLS", "MJF"]),
  buildX: z.number().positive(),
  buildY: z.number().positive(),
  buildZ: z.number().positive(),
  materials: z.array(z.string()).min(1),
});

const startPrintSchema = z.object({
  action: z.literal("start-print"),
  projectId: z.string(),
});

const bodySchema = z.discriminatedUnion("action", [addPrinterSchema, startPrintSchema]);

export async function POST(req: Request) {
  const parsed = bodySchema.safeParse(await req.json());
  if (!parsed.success) {
    return NextResponse.json({ error: parsed.error.flatten() }, { status: 400 });
  }
  const body = parsed.data;

  // Start a protected print: issue a single-use, short-lived G-code token that
  // the maker's OctoPrint/Klipper client uses to stream. No source is exposed.
  if (body.action === "start-print") {
    const token = issueGcodeStreamToken(`design-for-${body.projectId}`);
    if (!USE_MOCK_DATA) {
      const { prisma } = await import("@/lib/prisma");
      const project = await prisma.project.findUniqueOrThrow({
        where: { id: body.projectId },
        include: { printJob: true },
      });
      await prisma.printJob.upsert({
        where: { projectId: project.id },
        create: {
          projectId: project.id,
          printerId: project.printJob?.printerId ?? "",
          status: "STREAMING",
          gcodeStorageKey: token.gcodeStorageKey,
          gcodeExpiresAt: token.expiresAt,
          streamStartedAt: new Date(),
        },
        update: {
          status: "STREAMING",
          gcodeStorageKey: token.gcodeStorageKey,
          gcodeExpiresAt: token.expiresAt,
          streamStartedAt: new Date(),
        },
      });
    }
    return NextResponse.json({
      ok: true,
      streaming: true,
      expiresAt: token.expiresAt,
      note: "G-code temporaneo: scade dopo lo streaming, nessuna copia riutilizzabile.",
    });
  }

  // Add a printer.
  if (USE_MOCK_DATA) {
    return NextResponse.json({ ok: true, mock: true, printer: { id: `ptr_${Date.now()}`, ...body } }, { status: 201 });
  }
  const { prisma } = await import("@/lib/prisma");
  const printer = await prisma.printer.create({
    data: {
      makerId: body.makerId!,
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
