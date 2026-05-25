import { mkdir, readFile, writeFile, unlink, access } from "node:fs/promises";
import { dirname, join, normalize, resolve, sep } from "node:path";
import type { StorageProvider } from "./index";

// Filesystem-backed storage for local development. Not for production.
export class LocalStorage implements StorageProvider {
  private root: string;

  constructor() {
    this.root = resolve(process.env.FILE_STORAGE_LOCAL_DIR ?? ".storage");
  }

  // Resolve a key to an absolute path, guarding against traversal outside root.
  private pathFor(key: string): string {
    const safe = normalize(key).replace(/^(\.\.(\/|\\|$))+/, "");
    const full = join(this.root, safe);
    if (!resolve(full).startsWith(this.root + sep) && resolve(full) !== this.root) {
      throw new Error("Invalid storage key");
    }
    return full;
  }

  async put(key: string, bytes: Buffer): Promise<void> {
    const p = this.pathFor(key);
    await mkdir(dirname(p), { recursive: true });
    await writeFile(p, bytes);
  }

  async get(key: string): Promise<Buffer> {
    return readFile(this.pathFor(key));
  }

  async delete(key: string): Promise<void> {
    await unlink(this.pathFor(key)).catch(() => {});
  }

  async exists(key: string): Promise<boolean> {
    try {
      await access(this.pathFor(key));
      return true;
    } catch {
      return false;
    }
  }
}
