"use client";

import { useState } from "react";

/**
 * Pre-shipping QC approval. The maker uploads 3 HD photos of the printed part
 * on the bed; the client approves (or rejects) them. If the client does not
 * respond before `dueAt`, silent consent auto-approves and the shipping label
 * is generated.
 */
export function QCApproval({
  projectId,
  photoUrls,
  dueAt,
}: {
  projectId: string;
  photoUrls: string[];
  dueAt: string | null;
}) {
  const [state, setState] = useState<"idle" | "approved" | "rejected" | "loading">("idle");

  async function submit(decision: "approve" | "reject") {
    setState("loading");
    try {
      await fetch("/api/qc", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ projectId, decision }),
      });
      setState(decision === "approve" ? "approved" : "rejected");
    } catch {
      setState("idle");
    }
  }

  const deadline = dueAt ? new Date(dueAt) : null;
  const hoursLeft = deadline ? Math.max(0, Math.round((deadline.getTime() - Date.now()) / 3_600_000)) : null;

  return (
    <div>
      <div className="grid grid-cols-3 gap-3">
        {photoUrls.length === 0
          ? Array.from({ length: 3 }).map((_, i) => (
              <div
                key={i}
                className="grid aspect-square place-items-center rounded-lg border text-xs"
                style={{ background: "var(--surface-2)", borderColor: "var(--border)", color: "var(--muted)" }}
              >
                In attesa foto {i + 1}
              </div>
            ))
          : photoUrls.map((url, i) => (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                key={i}
                src={url}
                alt={`Foto QC ${i + 1}`}
                className="aspect-square w-full rounded-lg border object-cover"
                style={{ borderColor: "var(--border)" }}
              />
            ))}
      </div>

      {hoursLeft != null && state === "idle" && (
        <p className="mt-3 text-xs" style={{ color: "var(--muted)" }}>
          Silenzio assenso tra circa <strong>{hoursLeft}h</strong>: se non rispondi, le foto
          verranno approvate automaticamente.
        </p>
      )}

      <div className="mt-4 flex gap-3">
        {state === "approved" ? (
          <span className="text-sm font-medium" style={{ color: "var(--accent-2)" }}>
            ✓ Foto approvate — generazione etichetta in corso
          </span>
        ) : state === "rejected" ? (
          <span className="text-sm font-medium" style={{ color: "#ef4444" }}>
            Foto rifiutate — il maker è stato avvisato
          </span>
        ) : (
          <>
            <button
              disabled={state === "loading" || photoUrls.length === 0}
              onClick={() => submit("approve")}
              className="rounded-lg px-4 py-2 text-sm font-semibold text-white disabled:opacity-40"
              style={{ background: "var(--accent-2)" }}
            >
              Approva e spedisci
            </button>
            <button
              disabled={state === "loading" || photoUrls.length === 0}
              onClick={() => submit("reject")}
              className="rounded-lg border px-4 py-2 text-sm font-semibold disabled:opacity-40"
              style={{ borderColor: "var(--border)" }}
            >
              Richiedi modifiche
            </button>
          </>
        )}
      </div>
    </div>
  );
}
