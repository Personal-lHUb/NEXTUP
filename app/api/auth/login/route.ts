import { NextResponse } from "next/server";
import { z } from "zod";
import { cookies } from "next/headers";
import { findUserByEmail } from "@/lib/auth/users";
import { verifyPassword } from "@/lib/auth/password";
import { SESSION_COOKIE, cookieOptions, signSession } from "@/lib/auth/session";
import { firstRoleHome } from "@/lib/auth/guards";

const schema = z.object({ email: z.string().email(), password: z.string().min(1) });

export async function POST(req: Request) {
  const parsed = schema.safeParse(await req.json());
  if (!parsed.success) {
    return NextResponse.json({ error: "Dati non validi" }, { status: 400 });
  }
  const { email, password } = parsed.data;

  const user = await findUserByEmail(email);
  // Run a compare even when the user is missing to reduce timing leakage.
  const ok = user
    ? await verifyPassword(password, user.passwordHash)
    : await verifyPassword(password, "$2a$10$invalidinvalidinvalidinvalidinvalidinvalidinv");

  if (!user || !ok) {
    return NextResponse.json({ error: "Credenziali non valide" }, { status: 401 });
  }

  const token = await signSession({ id: user.id, email: user.email, name: user.name, roles: user.roles });
  (await cookies()).set(SESSION_COOKIE, token, cookieOptions());

  return NextResponse.json({
    ok: true,
    user: { id: user.id, email: user.email, name: user.name, roles: user.roles },
    redirect: firstRoleHome(user.roles),
  });
}
