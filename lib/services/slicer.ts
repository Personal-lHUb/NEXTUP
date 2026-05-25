import { execFile } from "node:child_process";
import { mkdtemp, readFile, writeFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { promisify } from "node:util";
import { parseStl } from "./stl";

const exec = promisify(execFile);

export interface SliceOptions {
  material?: string | null;
  layerHeightMm?: number;
  /** Source file extension, e.g. ".stl". */
  ext?: string;
}

export interface Slicer {
  slice(source: Buffer, opts?: SliceOptions): Promise<Buffer>;
}

/**
 * Invokes a real slicer CLI (PrusaSlicer / Slic3r / CuraEngine) when SLICER_BIN
 * is configured. Writes the source to a temp dir, runs the CLI, reads the
 * resulting G-code, then cleans up.
 */
class CliSlicer implements Slicer {
  constructor(private bin: string, private profile?: string) {}

  async slice(source: Buffer, opts: SliceOptions = {}): Promise<Buffer> {
    const dir = await mkdtemp(join(tmpdir(), "nextup-slice-"));
    const input = join(dir, `model${opts.ext ?? ".stl"}`);
    const output = join(dir, "model.gcode");
    try {
      await writeFile(input, source);
      const args = ["--export-gcode", "-o", output];
      if (this.profile) args.push("--load", this.profile);
      if (opts.layerHeightMm) args.push("--layer-height", String(opts.layerHeightMm));
      args.push(input);
      await exec(this.bin, args, { timeout: 5 * 60_000, maxBuffer: 64 * 1024 * 1024 });
      return await readFile(output);
    } finally {
      await rm(dir, { recursive: true, force: true });
    }
  }
}

/**
 * Deterministic placeholder slicer for environments without a slicer binary.
 * Produces minimal valid-looking G-code annotated with the model's dimensions
 * so the streaming pipeline can be exercised end-to-end.
 */
class MockSlicer implements Slicer {
  async slice(source: Buffer, opts: SliceOptions = {}): Promise<Buffer> {
    let dims = "unknown";
    try {
      if ((opts.ext ?? ".stl") === ".stl") {
        const m = parseStl(source);
        dims = `${m.boundingBoxX}x${m.boundingBoxY}x${m.boundingBoxZ} mm, ~${m.volumeCm3} cm3`;
      }
    } catch {
      /* ignore */
    }
    const gcode = [
      "; NextUp mock G-code (no slicer configured)",
      `; model: ${dims}`,
      `; material: ${opts.material ?? "n/a"}`,
      "M104 S200",
      "M109 S200",
      "G28 ; home",
      "G1 Z0.2 F600",
      "G1 X20 Y20 F3000",
      "; … sliced toolpath would follow …",
      "M104 S0",
      "M140 S0",
      "G28 X0",
      "M84 ; disable motors",
      "",
    ].join("\n");
    return Buffer.from(gcode, "utf8");
  }
}

let cached: Slicer | null = null;

export function getSlicer(): Slicer {
  if (cached) return cached;
  const bin = process.env.SLICER_BIN;
  cached = bin ? new CliSlicer(bin, process.env.SLICER_PROFILE || undefined) : new MockSlicer();
  return cached;
}
