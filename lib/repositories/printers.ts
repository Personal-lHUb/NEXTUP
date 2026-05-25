import { USE_MOCK_DATA } from "../constants";
import { MOCK_PRINTERS } from "../mock-data";
import type { PrinterVM } from "../types";

export async function getMakerPrinters(): Promise<PrinterVM[]> {
  if (USE_MOCK_DATA) return MOCK_PRINTERS;

  const { prisma } = await import("../prisma");
  const rows = await prisma.printer.findMany({ orderBy: { createdAt: "desc" } });
  return rows.map(
    (p): PrinterVM => ({
      id: p.id,
      name: p.name,
      technology: p.technology,
      buildX: p.buildX,
      buildY: p.buildY,
      buildZ: p.buildZ,
      materials: p.materials,
      status: p.status,
      octoprintConnected: Boolean(p.octoprintUrl && p.octoprintApiKey),
    }),
  );
}
