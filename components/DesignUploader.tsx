"use client";

import { useRef, useState } from "react";

interface UploadResult {
  filename: string;
  sizeBytes: number;
  metadata: { boundingBoxX: number; boundingBoxY: number; boundingBoxZ: number; volumeCm3: number | null };
}

export function DesignUploader() {
  const inputRef = useRef<HTMLInputElement>(null);
  const [status, setStatus] = useState<"idle" | "uploading" | "done" | "error">("idle");
  const [result, setResult] = useState<UploadResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function upload(file: File) {
    setStatus("uploading");
    setError(null);
    const form = new FormData();
    form.append("file", file);
    try {
      const res = await fetch("/api/designs/upload", { method: "POST", body: form });
      const data = await res.json();
      if (!res.ok) {
        setError(typeof data.error === "string" ? data.error : "Upload non riuscito");
        setStatus("error");
        return;
      }
      setResult(data);
      setStatus("done");
    } catch {
      setError("Errore di rete");
      setStatus("error");
    }
  }

  return (
    <div>
      <input
        ref={inputRef}
        type="file"
        accept=".stl,.obj,.3mf,.step,.stp"
        className="hidden"
        onChange={(e) => {
          const f = e.target.files?.[0];
          if (f) upload(f);
        }}
      />
      <button
        type="button"
        onClick={() => inputRef.current?.click()}
        disabled={status === "uploading"}
        className="grid w-full place-items-center rounded-lg border border-dashed py-10 text-sm disabled:opacity-60"
        style={{ borderColor: "var(--border)", color: "var(--muted)" }}
      >
        {status === "uploading"
          ? "Caricamento protetto in corso…"
          : "Clicca per caricare un file (STL/OBJ/3MF/STEP) — upload blindato"}
      </button>

      {error && <p className="mt-3 text-sm" style={{ color: "#ef4444" }}>{error}</p>}

      {status === "done" && result && (
        <div className="mt-4 rounded-lg border p-4 text-xs" style={{ borderColor: "var(--border)" }}>
          <p className="font-semibold" style={{ color: "var(--accent-2)" }}>
            ✓ {result.filename} caricato e blindato
          </p>
          <p className="mt-2" style={{ color: "var(--muted)" }}>
            Metadati tecnici estratti (gli unici dati visibili ai Maker):
          </p>
          <ul className="mt-1 space-y-0.5" style={{ color: "var(--text)" }}>
            <li>
              Ingombro: {result.metadata.boundingBoxX} × {result.metadata.boundingBoxY} ×{" "}
              {result.metadata.boundingBoxZ} mm
            </li>
            {result.metadata.volumeCm3 != null && <li>Volume: {result.metadata.volumeCm3} cm³</li>}
            <li>Dimensione file: {(result.sizeBytes / 1024).toFixed(1)} KB</li>
          </ul>
        </div>
      )}
    </div>
  );
}
