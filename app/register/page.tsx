"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

const ROLES = [
  { key: "CLIENT", label: "Cliente" },
  { key: "DESIGNER", label: "Progettista" },
  { key: "MAKER", label: "Maker" },
];

export default function RegisterPage() {
  const router = useRouter();
  const [form, setForm] = useState({ name: "", email: "", password: "" });
  const [roles, setRoles] = useState<string[]>(["CLIENT"]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  function toggleRole(role: string) {
    setRoles((prev) => (prev.includes(role) ? prev.filter((r) => r !== role) : [...prev, role]));
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (roles.length === 0) {
      setError("Seleziona almeno un ruolo");
      return;
    }
    setLoading(true);
    try {
      const res = await fetch("/api/auth/register", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ ...form, roles }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(typeof data.error === "string" ? data.error : "Registrazione non riuscita");
        return;
      }
      router.push(data.redirect || "/client");
      router.refresh();
    } catch {
      setError("Errore di rete");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto flex min-h-screen max-w-md flex-col justify-center px-6 py-10">
      <Link href="/" className="mb-8 flex items-center gap-2">
        <span className="grid h-8 w-8 place-items-center rounded-lg font-bold" style={{ background: "var(--accent)" }}>
          N
        </span>
        <span className="text-lg font-semibold">NextUp</span>
      </Link>

      <h1 className="text-2xl font-semibold">Crea un account</h1>

      <form onSubmit={submit} className="mt-6 space-y-4">
        <Field label="Nome">
          <input
            required
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            className="w-full rounded-lg border px-3 py-2 text-sm"
            style={{ background: "var(--surface-2)", borderColor: "var(--border)", color: "var(--text)" }}
          />
        </Field>
        <Field label="Email">
          <input
            type="email"
            required
            value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })}
            className="w-full rounded-lg border px-3 py-2 text-sm"
            style={{ background: "var(--surface-2)", borderColor: "var(--border)", color: "var(--text)" }}
          />
        </Field>
        <Field label="Password (min. 8 caratteri)">
          <input
            type="password"
            required
            minLength={8}
            value={form.password}
            onChange={(e) => setForm({ ...form, password: e.target.value })}
            className="w-full rounded-lg border px-3 py-2 text-sm"
            style={{ background: "var(--surface-2)", borderColor: "var(--border)", color: "var(--text)" }}
          />
        </Field>

        <div>
          <span className="mb-2 block text-sm" style={{ color: "var(--muted)" }}>Ruoli</span>
          <div className="flex gap-2">
            {ROLES.map((r) => (
              <button
                type="button"
                key={r.key}
                onClick={() => toggleRole(r.key)}
                className="rounded-lg border px-3 py-1.5 text-sm font-medium"
                style={
                  roles.includes(r.key)
                    ? { background: "var(--accent)", color: "white", borderColor: "var(--accent)" }
                    : { borderColor: "var(--border)", color: "var(--muted)" }
                }
              >
                {r.label}
              </button>
            ))}
          </div>
        </div>

        {error && <p className="text-sm" style={{ color: "#ef4444" }}>{error}</p>}

        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-lg px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-50"
          style={{ background: "var(--accent)" }}
        >
          {loading ? "Creazione…" : "Registrati"}
        </button>
      </form>

      <p className="mt-4 text-sm" style={{ color: "var(--muted)" }}>
        Hai già un account?{" "}
        <Link href="/login" style={{ color: "var(--accent)" }}>
          Accedi
        </Link>
      </p>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="mb-1 block text-sm" style={{ color: "var(--muted)" }}>{label}</span>
      {children}
    </label>
  );
}
