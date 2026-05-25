import { createHash, randomBytes } from "node:crypto";
import { USE_MOCK_DATA } from "../constants";
import { getStorage } from "../storage";
import { getProtectedSource } from "./file-protection";
import { getSlicer } from "./slicer";

// Orchestrates protected printing: slice the source server-side, stash the
// G-code under an ephemeral key, and hand the maker a single-use, short-lived
// token. The token is exchanged once for the byte stream, then invalidated and
// the ephemeral object is deleted — no reusable copy ever reaches the maker.

const TOKEN_TTL_S = Number(process.env.GCODE_TOKEN_TTL ?? 900);

export interface StartPrintInput {
  projectId: string;
  designStorageKey: string;
  ext?: string;
  material?: string | null;
}

export interface StartPrintResult {
  token: string;
  expiresAt: Date;
  bytes: number;
}

interface TokenRecord {
  gcodeStorageKey: string;
  expiresAt: number;
  consumed: boolean;
  projectId: string;
}

// In-memory token store for USE_MOCK_DATA mode (survives HMR via globalThis).
const globalForTokens = globalThis as unknown as { __nextupTokens?: Map<string, TokenRecord> };
const tokenStore = globalForTokens.__nextupTokens ?? new Map<string, TokenRecord>();
if (!globalForTokens.__nextupTokens) globalForTokens.__nextupTokens = tokenStore;

function hashToken(token: string): string {
  return createHash("sha256").update(token).digest("hex");
}

export async function startProtectedPrint(input: StartPrintInput): Promise<StartPrintResult> {
  const source = await getProtectedSource(input.designStorageKey);
  const gcode = await getSlicer().slice(source, { material: input.material, ext: input.ext ?? ".stl" });

  const storage = await getStorage();
  const gcodeStorageKey = `gcode-ephemeral/${randomBytes(16).toString("hex")}.gcode`;
  await storage.put(gcodeStorageKey, gcode, "text/plain");

  const token = randomBytes(24).toString("base64url");
  const expiresAt = new Date(Date.now() + TOKEN_TTL_S * 1000);
  const tokenHash = hashToken(token);

  if (USE_MOCK_DATA) {
    tokenStore.set(tokenHash, {
      gcodeStorageKey,
      expiresAt: expiresAt.getTime(),
      consumed: false,
      projectId: input.projectId,
    });
  } else {
    const { prisma } = await import("../prisma");
    const project = await prisma.project.findUniqueOrThrow({
      where: { id: input.projectId },
      include: { printJob: true },
    });
    await prisma.printJob.upsert({
      where: { projectId: project.id },
      create: {
        projectId: project.id,
        printerId: project.printJob?.printerId ?? "",
        status: "STREAMING",
        gcodeStorageKey,
        gcodeExpiresAt: expiresAt,
        streamTokenHash: tokenHash,
        streamStartedAt: new Date(),
      },
      update: {
        status: "STREAMING",
        gcodeStorageKey,
        gcodeExpiresAt: expiresAt,
        streamTokenHash: tokenHash,
        streamConsumedAt: null,
        streamStartedAt: new Date(),
      },
    });
  }

  return { token, expiresAt, bytes: gcode.byteLength };
}

/**
 * Exchanges a single-use token for the G-code bytes. Validates expiry + single
 * use, marks the token consumed, and deletes the ephemeral object. Returns null
 * if the token is invalid/expired/already used.
 */
export async function consumeStreamToken(token: string): Promise<Buffer | null> {
  const tokenHash = hashToken(token);
  const storage = await getStorage();

  if (USE_MOCK_DATA) {
    const rec = tokenStore.get(tokenHash);
    if (!rec || rec.consumed || rec.expiresAt < Date.now()) return null;
    rec.consumed = true;
    const bytes = await storage.get(rec.gcodeStorageKey).catch(() => null);
    await storage.delete(rec.gcodeStorageKey);
    return bytes;
  }

  const { prisma } = await import("../prisma");
  const job = await prisma.printJob.findFirst({ where: { streamTokenHash: tokenHash } });
  if (
    !job ||
    !job.gcodeStorageKey ||
    job.streamConsumedAt ||
    (job.gcodeExpiresAt && job.gcodeExpiresAt.getTime() < Date.now())
  ) {
    return null;
  }
  const bytes = await storage.get(job.gcodeStorageKey).catch(() => null);
  await storage.delete(job.gcodeStorageKey);
  await prisma.printJob.update({
    where: { id: job.id },
    data: { streamConsumedAt: new Date(), status: "PRINTING", gcodeStorageKey: null },
  });
  return bytes;
}
