// Storage abstraction for protected source files and ephemeral G-code.
// Source files are NEVER served to clients/makers directly — only read
// server-side for slicing.

export interface StorageProvider {
  put(key: string, bytes: Buffer, contentType?: string): Promise<void>;
  get(key: string): Promise<Buffer>;
  delete(key: string): Promise<void>;
  exists(key: string): Promise<boolean>;
}

let cached: StorageProvider | null = null;

export async function getStorage(): Promise<StorageProvider> {
  if (cached) return cached;
  const driver = process.env.STORAGE_DRIVER ?? "local";
  if (driver === "s3") {
    const { S3Storage } = await import("./s3");
    cached = new S3Storage();
  } else {
    const { LocalStorage } = await import("./local");
    cached = new LocalStorage();
  }
  return cached;
}
