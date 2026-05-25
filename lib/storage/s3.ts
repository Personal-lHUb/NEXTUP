import {
  S3Client,
  GetObjectCommand,
  PutObjectCommand,
  DeleteObjectCommand,
  HeadObjectCommand,
} from "@aws-sdk/client-s3";
import type { StorageProvider } from "./index";

// S3-compatible storage (AWS S3 / Cloudflare R2 / MinIO).
export class S3Storage implements StorageProvider {
  private client: S3Client;
  private bucket: string;

  constructor() {
    this.bucket = process.env.FILE_STORAGE_BUCKET ?? "nextup-protected-files";
    this.client = new S3Client({
      region: process.env.FILE_STORAGE_REGION ?? "auto",
      endpoint: process.env.FILE_STORAGE_ENDPOINT || undefined,
      forcePathStyle: (process.env.FILE_STORAGE_FORCE_PATH_STYLE ?? "true") === "true",
      credentials: {
        accessKeyId: process.env.FILE_STORAGE_ACCESS_KEY ?? "",
        secretAccessKey: process.env.FILE_STORAGE_SECRET_KEY ?? "",
      },
    });
  }

  async put(key: string, bytes: Buffer, contentType?: string): Promise<void> {
    await this.client.send(
      new PutObjectCommand({ Bucket: this.bucket, Key: key, Body: bytes, ContentType: contentType }),
    );
  }

  async get(key: string): Promise<Buffer> {
    const res = await this.client.send(new GetObjectCommand({ Bucket: this.bucket, Key: key }));
    const bytes = await res.Body!.transformToByteArray();
    return Buffer.from(bytes);
  }

  async delete(key: string): Promise<void> {
    await this.client.send(new DeleteObjectCommand({ Bucket: this.bucket, Key: key }));
  }

  async exists(key: string): Promise<boolean> {
    try {
      await this.client.send(new HeadObjectCommand({ Bucket: this.bucket, Key: key }));
      return true;
    } catch {
      return false;
    }
  }
}
