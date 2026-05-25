import { NextResponse } from "next/server";
import { USE_MOCK_DATA } from "@/lib/constants";
import { getCurrentUser } from "@/lib/auth/guards";
import { extractMetadata, storeProtectedSource } from "@/lib/services/file-protection";

const ALLOWED = [".stl", ".obj", ".3mf", ".step", ".stp"];

// Designer uploads a source model. Stored blinded; only metadata is returned.
export async function POST(req: Request) {
  const user = await getCurrentUser();
  if (!user) return NextResponse.json({ error: "Non autenticato" }, { status: 401 });
  if (!user.roles.includes("DESIGNER")) {
    return NextResponse.json({ error: "Ruolo non autorizzato" }, { status: 403 });
  }

  const form = await req.formData();
  const file = form.get("file");
  const projectId = form.get("projectId");

  if (!(file instanceof File)) {
    return NextResponse.json({ error: "File mancante" }, { status: 400 });
  }
  const filename = file.name;
  const ext = filename.slice(filename.lastIndexOf(".")).toLowerCase();
  if (!ALLOWED.includes(ext)) {
    return NextResponse.json({ error: `Formato non supportato: ${ext}` }, { status: 400 });
  }

  const bytes = Buffer.from(await file.arrayBuffer());
  const stored = await storeProtectedSource(bytes, filename);
  const metadata = extractMetadata(bytes, filename);

  if (!USE_MOCK_DATA) {
    const { prisma } = await import("@/lib/prisma");
    await prisma.designFile.create({
      data: {
        designerId: user.id,
        projectId: typeof projectId === "string" && projectId ? projectId : undefined,
        filename,
        format: ext === ".stl" ? "STL" : ext === ".obj" ? "OBJ" : ext === ".3mf" ? "THREE_MF" : "STEP",
        storageKey: stored.storageKey,
        fileHash: stored.fileHash,
        sizeBytes: stored.sizeBytes,
        boundingBoxX: metadata.boundingBoxX,
        boundingBoxY: metadata.boundingBoxY,
        boundingBoxZ: metadata.boundingBoxZ,
        volumeCm3: metadata.volumeCm3,
      },
    });
  }

  // Only derived metadata is returned to the client — never anything that lets
  // a third party reconstruct the geometry.
  return NextResponse.json(
    {
      ok: true,
      filename,
      sizeBytes: stored.sizeBytes,
      metadata,
    },
    { status: 201 },
  );
}
