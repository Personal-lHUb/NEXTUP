import type { ProjectStatus } from "@prisma/client";

const LABELS: Record<string, { text: string; color: string }> = {
  DRAFT: { text: "Bozza", color: "#95a0b8" },
  MODELING: { text: "In modellazione", color: "#5b6bff" },
  MODEL_REVIEW: { text: "Revisione render", color: "#5b6bff" },
  MODEL_APPROVED: { text: "Render approvato", color: "#22d3a8" },
  MATCHING: { text: "Ricerca maker", color: "#eab308" },
  PRINTING: { text: "In stampa", color: "#f97316" },
  QC_PENDING: { text: "Controllo qualità", color: "#eab308" },
  QC_APPROVED: { text: "QC approvato", color: "#22d3a8" },
  SHIPPING: { text: "In spedizione", color: "#06b6d4" },
  DELIVERED: { text: "Consegnato", color: "#22d3a8" },
  COMPLETED: { text: "Completato", color: "#22d3a8" },
  CANCELLED: { text: "Annullato", color: "#ef4444" },
  DISPUTED: { text: "In disputa", color: "#ef4444" },
};

export function StatusBadge({ status }: { status: ProjectStatus | string }) {
  const meta = LABELS[status] ?? { text: status, color: "#95a0b8" };
  return (
    <span
      style={{
        color: meta.color,
        borderColor: meta.color,
      }}
      className="inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-medium"
    >
      <span className="h-1.5 w-1.5 rounded-full" style={{ background: meta.color }} />
      {meta.text}
    </span>
  );
}
