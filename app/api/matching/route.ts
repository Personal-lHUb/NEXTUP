import { NextResponse } from "next/server";
import { z } from "zod";
import { USE_MOCK_DATA } from "@/lib/constants";
import { compatibleJobs } from "@/lib/services/matching";
import { getOpenJobs } from "@/lib/repositories/projects";
import { getMakerPrinters } from "@/lib/repositories/printers";
import { MOCK_PRINTERS } from "@/lib/mock-data";

const querySchema = z.object({ printerId: z.string() });

// Returns open jobs compatible with a given printer (volume + materials).
export async function GET(req: Request) {
  const { searchParams } = new URL(req.url);
  const parsed = querySchema.safeParse({ printerId: searchParams.get("printerId") });
  if (!parsed.success) {
    return NextResponse.json({ error: "printerId is required" }, { status: 400 });
  }

  const printers = USE_MOCK_DATA ? MOCK_PRINTERS : await getMakerPrinters();
  const printer = printers.find((p) => p.id === parsed.data.printerId);
  if (!printer) return NextResponse.json({ error: "printer not found" }, { status: 404 });

  const jobs = await getOpenJobs();
  const matches = compatibleJobs(
    {
      buildX: printer.buildX,
      buildY: printer.buildY,
      buildZ: printer.buildZ,
      technology: printer.technology,
      materials: printer.materials,
    },
    jobs.map((j) => ({ ...j })),
  );

  return NextResponse.json({ printerId: printer.id, jobs: matches });
}
