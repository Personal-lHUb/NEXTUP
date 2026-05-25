import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { SESSION_COOKIE, verifySession, type SessionUser } from "./session";

// Server-side helpers for route handlers and server components.

export async function getCurrentUser(): Promise<SessionUser | null> {
  const store = await cookies();
  return verifySession(store.get(SESSION_COOKIE)?.value);
}

/** Redirects to /login when there is no valid session. */
export async function requireUser(): Promise<SessionUser> {
  const user = await getCurrentUser();
  if (!user) redirect("/login");
  return user;
}

/**
 * Requires the session user to hold a specific role. Unauthenticated users go
 * to /login; authenticated users lacking the role are sent to the landing page.
 */
export async function requireRole(role: "CLIENT" | "DESIGNER" | "MAKER" | "ADMIN"): Promise<SessionUser> {
  const user = await getCurrentUser();
  if (!user) redirect(`/login?next=${roleHome(role)}`);
  if (!user.roles.includes(role)) redirect("/");
  return user;
}

export function roleHome(role: string): string {
  switch (role) {
    case "MAKER":
      return "/maker";
    case "DESIGNER":
      return "/designer";
    default:
      return "/client";
  }
}

export function firstRoleHome(roles: string[]): string {
  if (roles.includes("CLIENT")) return "/client";
  if (roles.includes("MAKER")) return "/maker";
  if (roles.includes("DESIGNER")) return "/designer";
  return "/";
}
