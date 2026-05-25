"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

export function LogoutButton() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);

  async function logout() {
    setLoading(true);
    await fetch("/api/auth/logout", { method: "POST" }).catch(() => {});
    router.push("/login");
    router.refresh();
  }

  return (
    <button
      onClick={logout}
      disabled={loading}
      className="rounded-md border px-3 py-1.5 text-sm font-medium disabled:opacity-50"
      style={{ borderColor: "var(--border)", color: "var(--muted)" }}
    >
      {loading ? "…" : "Esci"}
    </button>
  );
}
