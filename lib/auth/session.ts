import { SignJWT, jwtVerify } from "jose";

// Edge-safe session layer (jose only — no node:crypto / bcrypt imports here, so
// it can be used from middleware as well as route handlers).

export const SESSION_COOKIE = "nextup_session";
export const SESSION_MAX_AGE = Number(process.env.SESSION_MAX_AGE ?? 604_800); // 7d

export interface SessionUser {
  id: string;
  email: string;
  name: string;
  roles: string[];
}

function secret(): Uint8Array {
  const s = process.env.AUTH_SECRET ?? "dev-only-insecure-secret-change-me";
  return new TextEncoder().encode(s);
}

export async function signSession(user: SessionUser): Promise<string> {
  return new SignJWT({ email: user.email, name: user.name, roles: user.roles })
    .setProtectedHeader({ alg: "HS256" })
    .setSubject(user.id)
    .setIssuedAt()
    .setExpirationTime(`${SESSION_MAX_AGE}s`)
    .sign(secret());
}

export async function verifySession(token: string | undefined | null): Promise<SessionUser | null> {
  if (!token) return null;
  try {
    const { payload } = await jwtVerify(token, secret());
    return {
      id: String(payload.sub),
      email: String(payload.email),
      name: String(payload.name),
      roles: (payload.roles as string[]) ?? [],
    };
  } catch {
    return null;
  }
}

export function cookieOptions() {
  return {
    httpOnly: true,
    sameSite: "lax" as const,
    secure: process.env.NODE_ENV === "production",
    path: "/",
    maxAge: SESSION_MAX_AGE,
  };
}
