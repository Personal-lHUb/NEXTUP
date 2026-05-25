import { NextResponse } from "next/server";
import { z } from "zod";
import { USE_MOCK_DATA } from "@/lib/constants";
import { getCurrentUser } from "@/lib/auth/guards";
import { startProtectedPrint } from "@/lib/services/print";
import { storeProtectedSource } from "@/lib/services/file-protection";
import { demoCubeStl } from "@/lib/services/demo-stl";

const schema = z.object({
  projectId: z.string(),
  designStorageKey: z.string().optional(),
  material: z.string().optional(),
});

// Maker starts a protected print. Slices server-side and returns a single-use
// token the printer agent exchanges for the G-code stream. No source exposed.
export async function POST(req: Request) {
  const user = await getCurrentUser();
  if (!user) return NextResponse.json({ error: "Non autenticato" }, { status: 401 });
  if (!user.roles.includes("MAKER")) {
    return NextResponse.json({ error: "Ruolo non autorizzato" }, { status: 403 });
  }

  const parsed = schema.safeParse(await req.json());
  if (!parsed.success) {
    return NextResponse.json({ error: parsed.error.flatten() }, { status: 400 });
  }
  const { projectId, material } = parsed.data;

  let designStorageKey = parsed.data.designStorageKey;
  if (!designStorageKey) {
    if (USE_MOCK_DATA) {
      // No real upload in mock mode: synthesize a source so the pipeline runs.
      const up = await storeProtectedSource(demoCubeStl(30), "demo.stl");
      designStorageKey = up.storageKey;
    } else {
      const { prisma } = await import("@/lib/prisma");
      const df = await prisma.designFile.findFirst({ where: { projectId } });
      if (!df) return NextResponse.json({ error: "Nessun file sorgente per il progetto" }, { status: 400 });
      designStorageKey = df.storageKey;
    }
  }

  const result = await startProtectedPrint({ projectId, designStorageKey, ext: ".stl", material });

  return NextResponse.json({
    ok: true,
    streamUrl: `/api/print/stream?token=${result.token}`,
    expiresAt: result.expiresAt,
    bytes: result.bytes,
    note: "Token monouso: scade dopo lo streaming, nessuna copia riutilizzabile.",
  });
}
