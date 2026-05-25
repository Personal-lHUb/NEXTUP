"use client";

import { useMemo, useState } from "react";
import type { JobVM, PrinterVM } from "@/lib/types";
import { isCompatible } from "@/lib/services/matching";
import { formatEUR } from "@/lib/money";

/**
 * Maker "Find Jobs" board. Jobs are filtered to those compatible with the
 * selected printer's build volume + materials. Only technical metadata is ever
 * shown — never the source file.
 */
export function JobBoard({ printers, jobs }: { printers: PrinterVM[]; jobs: JobVM[] }) {
  const [printerId, setPrinterId] = useState(printers[0]?.id ?? "");
  const [onlyCompatible, setOnlyCompatible] = useState(true);

  const selected = printers.find((p) => p.id === printerId);

  const visible = useMemo(() => {
    if (!selected || !onlyCompatible) return jobs;
    return jobs.filter((job) =>
      isCompatible(
        {
          buildX: selected.buildX,
          buildY: selected.buildY,
          buildZ: selected.buildZ,
          technology: selected.technology,
          materials: selected.materials,
        },
        {
          requiredX: job.requiredX,
          requiredY: job.requiredY,
          requiredZ: job.requiredZ,
          material: job.material,
        },
      ),
    );
  }, [selected, onlyCompatible, jobs]);

  return (
    <div>
      <div className="mb-4 flex flex-wrap items-center gap-4">
        <label className="text-sm" style={{ color: "var(--muted)" }}>
          Stampante:{" "}
          <select
            value={printerId}
            onChange={(e) => setPrinterId(e.target.value)}
            className="rounded-md border px-2 py-1 text-sm"
            style={{ background: "var(--surface-2)", borderColor: "var(--border)", color: "var(--text)" }}
          >
            {printers.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name} ({p.buildX}×{p.buildY}×{p.buildZ})
              </option>
            ))}
          </select>
        </label>
        <label className="flex items-center gap-2 text-sm" style={{ color: "var(--muted)" }}>
          <input
            type="checkbox"
            checked={onlyCompatible}
            onChange={(e) => setOnlyCompatible(e.target.checked)}
          />
          Solo lavori compatibili
        </label>
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        {visible.length === 0 ? (
          <p className="text-sm" style={{ color: "var(--muted)" }}>
            Nessun lavoro compatibile con questa stampante al momento.
          </p>
        ) : (
          visible.map((job) => <JobRow key={job.id} job={job} />)
        )}
      </div>
    </div>
  );
}

function JobRow({ job }: { job: JobVM }) {
  const [started, setStarted] = useState(false);

  async function startPrint() {
    setStarted(true);
    await fetch("/api/printers", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ action: "start-print", projectId: job.id }),
    }).catch(() => {});
  }

  return (
    <div
      className="rounded-lg border p-4"
      style={{ background: "var(--surface-2)", borderColor: "var(--border)" }}
    >
      <div className="mb-2 flex items-start justify-between">
        <h3 className="text-sm font-semibold">{job.title}</h3>
        {job.printPrice != null && (
          <span className="text-sm font-semibold" style={{ color: "var(--accent-2)" }}>
            {formatEUR(job.printPrice)}
          </span>
        )}
      </div>
      <dl className="space-y-1 text-xs" style={{ color: "var(--muted)" }}>
        <div className="flex justify-between">
          <dt>Ingombro</dt>
          <dd style={{ color: "var(--text)" }}>
            {job.requiredX} × {job.requiredY} × {job.requiredZ} mm
          </dd>
        </div>
        {job.volumeCm3 != null && (
          <div className="flex justify-between">
            <dt>Volume materiale</dt>
            <dd style={{ color: "var(--text)" }}>{job.volumeCm3} cm³</dd>
          </div>
        )}
        {job.material && (
          <div className="flex justify-between">
            <dt>Materiale</dt>
            <dd style={{ color: "var(--text)" }}>{job.material}</dd>
          </div>
        )}
      </dl>
      <p className="mt-2 text-[11px] italic" style={{ color: "var(--muted)" }}>
        File sorgente non scaricabile — stampa via streaming protetto.
      </p>
      <button
        onClick={startPrint}
        disabled={started}
        className="mt-3 w-full rounded-lg px-3 py-2 text-sm font-semibold text-white disabled:opacity-50"
        style={{ background: "var(--accent)" }}
      >
        {started ? "Stampa avviata (streaming G-code)" : "Avvia stampa protetta"}
      </button>
    </div>
  );
}
