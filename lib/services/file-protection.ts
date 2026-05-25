import { createHash, randomBytes } from "node:crypto";
import { extname } from "node:path";
import { getStorage } from "../storage";
import { parseStl } from "./stl";

/**
 * IP-protection layer for source geometry (STL/OBJ/3MF/STEP).
 *
 *  - Source files live in the protected object store; clients/makers can NEVER
 *    download them. They are only ever read server-side, for slicing.
 *  - Makers only receive derived technical metadata (bounding box, volume).
 *  - Printing happens via server-side slicing + a single-use, short-lived
 *    G-code stream (see lib/services/print.ts).
 */

export interface ProtectedUploadResult {
  storageKey: string;
  fileHash: string;
  sizeBytes: number;
}

export interface SourceMetadata {
  boundingBoxX: number;
  boundingBoxY: number;
  boundingBoxZ: number;
  volumeCm3: number | null;
}

/** Stores raw source bytes in the protected bucket and returns a content hash. */
export async function storeProtectedSource(
  bytes: Buffer,
  filename: string,
): Promise<ProtectedUploadResult> {
  const fileHash = createHash("sha256").update(bytes).digest("hex");
  const ext = extname(filename).toLowerCase() || ".bin";
  const storageKey = `protected/${fileHash}-${randomBytes(6).toString("hex")}${ext}`;
  const storage = await getStorage();
  await storage.put(storageKey, bytes, "application/octet-stream");
  return { storageKey, fileHash, sizeBytes: bytes.byteLength };
}

/**
 * Reads a protected source file. SERVER-ONLY: never call this from a code path
 * that returns the bytes to a client or maker. Used exclusively by the slicer.
 */
export async function getProtectedSource(storageKey: string): Promise<Buffer> {
  const storage = await getStorage();
  return storage.get(storageKey);
}

/** Derives the technical metadata exposed to makers from source bytes. */
export function extractMetadata(bytes: Buffer, filename: string): SourceMetadata {
  const ext = extname(filename).toLowerCase();
  if (ext === ".stl") {
    const m = parseStl(bytes);
    return {
      boundingBoxX: m.boundingBoxX,
      boundingBoxY: m.boundingBoxY,
      boundingBoxZ: m.boundingBoxZ,
      volumeCm3: m.volumeCm3,
    };
  }
  // TODO: OBJ/3MF/STEP parsers. Return empty bbox until implemented.
  return { boundingBoxX: 0, boundingBoxY: 0, boundingBoxZ: 0, volumeCm3: null };
}

/**
 * Returns the ONLY information a maker is allowed to see about a model.
 * Never returns geometry, the storage key, or anything downloadable.
 */
export function publicMetadata(meta: SourceMetadata) {
  return {
    boundingBoxX: meta.boundingBoxX,
    boundingBoxY: meta.boundingBoxY,
    boundingBoxZ: meta.boundingBoxZ,
    volumeCm3: meta.volumeCm3,
  };
}
