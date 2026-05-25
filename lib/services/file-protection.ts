import { randomBytes, createHash } from "node:crypto";

/**
 * IP-protection layer for source geometry (STL/OBJ/3MF/STEP).
 *
 * Design principles:
 *  - Source files live in a private object store; makers can NEVER download them.
 *  - Makers only ever receive derived technical metadata (bounding box, volume).
 *  - To print, the platform slices server-side and streams a single-use,
 *    short-lived G-code token to the maker's printer (OctoPrint/Klipper).
 *    The token expires after the stream, so no reusable copy is left behind.
 *
 * This module is a stub: storage and slicing are not yet wired to real backends,
 * but the interfaces and security contract are in place.
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

export interface GcodeStreamToken {
  token: string;
  /** Single-use key the streaming endpoint validates. */
  gcodeStorageKey: string;
  expiresAt: Date;
}

/** Stores raw source bytes in the protected bucket and returns a content hash. */
export async function storeProtectedSource(bytes: Buffer): Promise<ProtectedUploadResult> {
  const fileHash = createHash("sha256").update(bytes).digest("hex");
  const storageKey = `protected/${fileHash}-${randomBytes(8).toString("hex")}`;
  // TODO: upload `bytes` to FILE_STORAGE_BUCKET via the storage client.
  return { storageKey, fileHash, sizeBytes: bytes.byteLength };
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

/**
 * Issues a single-use, time-boxed token used to stream G-code to the maker's
 * printer. The maker's client presents the token; the stream endpoint slices
 * server-side and pushes to the printer, then invalidates the token.
 */
export function issueGcodeStreamToken(
  designStorageKey: string,
  ttlMs = 15 * 60_000,
): GcodeStreamToken {
  const token = randomBytes(24).toString("base64url");
  const gcodeStorageKey = `gcode-ephemeral/${createHash("sha256")
    .update(designStorageKey + token)
    .digest("hex")}`;
  return { token, gcodeStorageKey, expiresAt: new Date(Date.now() + ttlMs) };
}
