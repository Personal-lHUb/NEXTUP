import Link from "next/link";
import { LogoutButton } from "./LogoutButton";

type RoleKey = "client" | "maker" | "designer";

const NAV: { key: RoleKey; href: "/client" | "/maker" | "/designer"; label: string; role: string }[] = [
  { key: "client", href: "/client", label: "Cliente", role: "CLIENT" },
  { key: "maker", href: "/maker", label: "Maker", role: "MAKER" },
  { key: "designer", href: "/designer", label: "Progettista", role: "DESIGNER" },
];

export function DashboardShell({
  active,
  title,
  subtitle,
  user,
  children,
}: {
  active: RoleKey;
  title: string;
  subtitle?: string;
  user?: { name: string; roles: string[] };
  children: React.ReactNode;
}) {
  const roles = user?.roles ?? [];
  const nav = user ? NAV.filter((item) => roles.includes(item.role)) : NAV;

  return (
    <div className="min-h-screen">
      <header className="border-b" style={{ borderColor: "var(--border)" }}>
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <Link href="/" className="flex items-center gap-2">
            <span
              className="grid h-8 w-8 place-items-center rounded-lg font-bold"
              style={{ background: "var(--accent)" }}
            >
              N
            </span>
            <span className="text-lg font-semibold">NextUp</span>
          </Link>

          <div className="flex items-center gap-3">
            <nav className="flex items-center gap-1 rounded-lg p-1" style={{ background: "var(--surface)" }}>
              {nav.map((item) => (
                <Link
                  key={item.key}
                  href={item.href}
                  className="rounded-md px-3 py-1.5 text-sm font-medium transition-colors"
                  style={
                    item.key === active
                      ? { background: "var(--accent)", color: "white" }
                      : { color: "var(--muted)" }
                  }
                >
                  {item.label}
                </Link>
              ))}
            </nav>
            {user && (
              <div className="flex items-center gap-3">
                <span className="hidden text-sm sm:inline" style={{ color: "var(--muted)" }}>
                  {user.name}
                </span>
                <LogoutButton />
              </div>
            )}
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-6 py-8">
        <div className="mb-6">
          <h1 className="text-2xl font-semibold">{title}</h1>
          {subtitle && <p className="mt-1 text-sm" style={{ color: "var(--muted)" }}>{subtitle}</p>}
        </div>
        {children}
      </main>
    </div>
  );
}

export function Card({
  children,
  className = "",
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      className={`rounded-xl border p-5 ${className}`}
      style={{ background: "var(--surface)", borderColor: "var(--border)" }}
    >
      {children}
    </div>
  );
}
