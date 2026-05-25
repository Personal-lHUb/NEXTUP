import { NextResponse, type NextRequest } from "next/server";
import { SESSION_COOKIE, verifySession } from "@/lib/auth/session";

// Maps protected path prefixes to the role required to enter them.
const ROLE_GATES: { prefix: string; role: string }[] = [
  { prefix: "/client", role: "CLIENT" },
  { prefix: "/maker", role: "MAKER" },
  { prefix: "/designer", role: "DESIGNER" },
];

export async function middleware(req: NextRequest) {
  const { pathname } = req.nextUrl;
  const gate = ROLE_GATES.find((g) => pathname === g.prefix || pathname.startsWith(`${g.prefix}/`));
  if (!gate) return NextResponse.next();

  const user = await verifySession(req.cookies.get(SESSION_COOKIE)?.value);

  if (!user) {
    const url = req.nextUrl.clone();
    url.pathname = "/login";
    url.searchParams.set("next", pathname);
    return NextResponse.redirect(url);
  }

  if (!user.roles.includes(gate.role)) {
    const url = req.nextUrl.clone();
    url.pathname = "/";
    return NextResponse.redirect(url);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/client/:path*", "/maker/:path*", "/designer/:path*"],
};
