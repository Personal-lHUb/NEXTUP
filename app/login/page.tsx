"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.error ?? "Accesso non riuscito");
        return;
      }
      const next = new URLSearchParams(window.location.search).get("next");
      router.push(next || data.redirect || "/client");
      router.refresh();
    } catch {
      setError("Errore di rete");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto flex min-h-screen max-w-md flex-col justify-center px-6">
      <Link href="/" className="mb-8 flex items-center gap-2">
        <span className="grid h-8 w-8 place-items-center rounded-lg font-bold" style={{ background: "var(--accent)" }}>
          N
        </span>
        <span className="text-lg font-semibold">NextUp</span>
      </Link>

      <h1 className="text-2xl font-semibold">Accedi</h1>
      <p className="mt-1 text-sm" style={{ color: "var(--muted)" }}>
        Bentornato. Inserisci le tue credenziali.
      </p>

      <form onSubmit={submit} className="mt-6 space-y-4">
        <Field label="Email">
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full rounded-lg border px-3 py-2 text-sm"
            style={{ background: "var(--surface-2)", borderColor: "var(--border)", color: "var(--text)" }}
          />
        </Field>
        <Field label="Password">
          <input
            type="password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full rounded-lg border px-3 py-2 text-sm"
            style={{ background: "var(--surface-2)", borderColor: "var(--border)", color: "var(--text)" }}
          />
        </Field>

        {error && <p className="text-sm" style={{ color: "#ef4444" }}>{error}</p>}

        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-lg px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-50"
          style={{ background: "var(--accent)" }}
        >
          {loading ? "Accesso…" : "Accedi"}
        </button>
      </form>

      <p className="mt-4 text-sm" style={{ color: "var(--muted)" }}>
        Non hai un account?{" "}
        <Link href="/register" style={{ color: "var(--accent)" }}>
          Registrati
        </Link>
      </p>

      <div className="mt-8 rounded-lg border p-4 text-xs" style={{ borderColor: "var(--border)", color: "var(--muted)" }}>
        <p className="font-semibold" style={{ color: "var(--text)" }}>Account demo (modalità mock)</p>
        <p className="mt-1">demo@nextup.dev · password: demo1234 — tutti i ruoli</p>
        <p>giulia@example.com (cliente) · marco@example.com (designer) · andrea@example.com (maker)</p>
      </div>
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
