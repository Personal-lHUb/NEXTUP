// Minimal STL parser (binary + ASCII) used to derive the technical metadata
// makers are allowed to see: bounding box and material volume. Runs server-side
// only — geometry never leaves the platform.

export interface StlMetadata {
  triangleCount: number;
  boundingBoxX: number; // mm
  boundingBoxY: number;
  boundingBoxZ: number;
  volumeCm3: number;
}

type Vec3 = [number, number, number];

function isBinary(buf: Buffer): boolean {
  if (buf.length < 84) return false;
  const count = buf.readUInt32LE(80);
  return buf.length === 84 + count * 50;
}

function signedVolume(a: Vec3, b: Vec3, c: Vec3): number {
  // (a · (b × c)) / 6
  const cross: Vec3 = [
    b[1] * c[2] - b[2] * c[1],
    b[2] * c[0] - b[0] * c[2],
    b[0] * c[1] - b[1] * c[0],
  ];
  return (a[0] * cross[0] + a[1] * cross[1] + a[2] * cross[2]) / 6;
}

class Accumulator {
  min: Vec3 = [Infinity, Infinity, Infinity];
  max: Vec3 = [-Infinity, -Infinity, -Infinity];
  volMm3 = 0;
  count = 0;

  addTriangle(a: Vec3, b: Vec3, c: Vec3) {
    for (const v of [a, b, c]) {
      for (let i = 0; i < 3; i++) {
        if (v[i] < this.min[i]) this.min[i] = v[i];
        if (v[i] > this.max[i]) this.max[i] = v[i];
      }
    }
    this.volMm3 += signedVolume(a, b, c);
    this.count++;
  }

  result(): StlMetadata {
    const dim = (i: number) => (this.count ? Math.round((this.max[i] - this.min[i]) * 100) / 100 : 0);
    return {
      triangleCount: this.count,
      boundingBoxX: dim(0),
      boundingBoxY: dim(1),
      boundingBoxZ: dim(2),
      volumeCm3: Math.round((Math.abs(this.volMm3) / 1000) * 100) / 100,
    };
  }
}

function parseBinary(buf: Buffer): StlMetadata {
  const acc = new Accumulator();
  const count = buf.readUInt32LE(80);
  let offset = 84;
  for (let i = 0; i < count; i++) {
    offset += 12; // skip normal
    const read = (): Vec3 => {
      const v: Vec3 = [buf.readFloatLE(offset), buf.readFloatLE(offset + 4), buf.readFloatLE(offset + 8)];
      offset += 12;
      return v;
    };
    const a = read();
    const b = read();
    const c = read();
    offset += 2; // attribute byte count
    acc.addTriangle(a, b, c);
  }
  return acc.result();
}

function parseAscii(text: string): StlMetadata {
  const acc = new Accumulator();
  const verts: Vec3[] = [];
  const re = /vertex\s+(-?[\d.eE+]+)\s+(-?[\d.eE+]+)\s+(-?[\d.eE+]+)/g;
  let m: RegExpExecArray | null;
  while ((m = re.exec(text))) {
    verts.push([parseFloat(m[1]), parseFloat(m[2]), parseFloat(m[3])]);
    if (verts.length === 3) {
      acc.addTriangle(verts[0], verts[1], verts[2]);
      verts.length = 0;
    }
  }
  return acc.result();
}

export function parseStl(buf: Buffer): StlMetadata {
  return isBinary(buf) ? parseBinary(buf) : parseAscii(buf.toString("utf8"));
}
