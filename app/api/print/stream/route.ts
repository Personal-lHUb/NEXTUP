import { NextResponse } from "next/server";
import { consumeStreamToken } from "@/lib/services/print";

// Single-use G-code stream. The printer agent presents the token exactly once;
// the bytes are returned and the ephemeral object is destroyed. Subsequent
// requests with the same token return 410 Gone.
export async function GET(req: Request) {
  const token = new URL(req.url).searchParams.get("token");
  if (!token) return NextResponse.json({ error: "Token mancante" }, { status: 400 });

  const gcode = await consumeStreamToken(token);
  if (!gcode) {
    return NextResponse.json({ error: "Token non valido, scaduto o già usato" }, { status: 410 });
  }

  return new Response(new Uint8Array(gcode), {
    status: 200,
    headers: {
      "content-type": "text/plain; charset=utf-8",
      "content-disposition": 'attachment; filename="print.gcode"',
      "cache-control": "no-store",
    },
  });
}
