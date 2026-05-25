// Generates a binary STL of an axis-aligned cube. Used in mock mode to exercise
// the slicing/streaming pipeline without a real uploaded model.

type Vec3 = [number, number, number];

export function demoCubeStl(sizeMm = 30): Buffer {
  const s = sizeMm;
  const v: Vec3[] = [
    [0, 0, 0],
    [s, 0, 0],
    [s, s, 0],
    [0, s, 0],
    [0, 0, s],
    [s, 0, s],
    [s, s, s],
    [0, s, s],
  ];
  // 12 triangles (two per face), CCW.
  const tris: [number, number, number][] = [
    [0, 1, 2], [0, 2, 3], // bottom
    [4, 6, 5], [4, 7, 6], // top
    [0, 4, 5], [0, 5, 1], // front
    [1, 5, 6], [1, 6, 2], // right
    [2, 6, 7], [2, 7, 3], // back
    [3, 7, 4], [3, 4, 0], // left
  ];

  const buf = Buffer.alloc(84 + tris.length * 50);
  buf.write("NextUp demo cube", 0);
  buf.writeUInt32LE(tris.length, 80);

  let off = 84;
  for (const [a, b, c] of tris) {
    // normal (zeroed — not needed for our metadata)
    buf.writeFloatLE(0, off); buf.writeFloatLE(0, off + 4); buf.writeFloatLE(0, off + 8);
    off += 12;
    for (const idx of [a, b, c]) {
      buf.writeFloatLE(v[idx][0], off);
      buf.writeFloatLE(v[idx][1], off + 4);
      buf.writeFloatLE(v[idx][2], off + 8);
      off += 12;
    }
    buf.writeUInt16LE(0, off);
    off += 2;
  }
  return buf;
}
