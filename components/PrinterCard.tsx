import type { PrinterVM } from "@/lib/types";

const STATUS_LABEL: Record<string, { text: string; color: string }> = {
  ACTIVE: { text: "Attiva", color: "#22d3a8" },
  INACTIVE: { text: "Inattiva", color: "#95a0b8" },
  BUSY: { text: "Occupata", color: "#f97316" },
};

export function PrinterCard({ printer }: { printer: PrinterVM }) {
  const s = STATUS_LABEL[printer.status] ?? STATUS_LABEL.INACTIVE;
  return (
    <div
      className="rounded-lg border p-4"
      style={{ background: "var(--surface-2)", borderColor: "var(--border)" }}
    >
      <div className="mb-2 flex items-start justify-between">
        <div>
          <h3 className="text-sm font-semibold">{printer.name}</h3>
          <p className="text-xs" style={{ color: "var(--muted)" }}>
            {printer.technology}
          </p>
        </div>
        <span className="text-xs font-medium" style={{ color: s.color }}>
          ● {s.text}
        </span>
      </div>
      <dl className="space-y-1 text-xs" style={{ color: "var(--muted)" }}>
        <div className="flex justify-between">
          <dt>Volume di stampa</dt>
          <dd style={{ color: "var(--text)" }}>
            {printer.buildX} × {printer.buildY} × {printer.buildZ} mm
          </dd>
        </div>
        <div className="flex justify-between">
          <dt>Materiali</dt>
          <dd className="text-right" style={{ color: "var(--text)" }}>
            {printer.materials.join(", ")}
          </dd>
        </div>
        <div className="flex justify-between">
          <dt>OctoPrint/Klipper</dt>
          <dd style={{ color: printer.octoprintConnected ? "var(--accent-2)" : "var(--muted)" }}>
            {printer.octoprintConnected ? "Collegata" : "Non collegata"}
          </dd>
        </div>
      </dl>
    </div>
  );
}
