import type { ProjectVM } from "@/lib/types";
import { macroPhase } from "@/lib/types";
import { ProjectCard } from "./ProjectCard";

/**
 * Client Kanban split into the two macro-phases from the spec:
 * "In Modellazione" (dialogue with the Designer) and "In Stampa" (dialogue
 * with the Maker). Completed/closed projects appear in a third column.
 */
export function KanbanBoard({ projects }: { projects: ProjectVM[] }) {
  const closedStatuses = ["COMPLETED", "DELIVERED", "CANCELLED"];

  const modeling = projects.filter(
    (p) => !closedStatuses.includes(p.status) && macroPhase(p.status) === "MODELING",
  );
  const printing = projects.filter(
    (p) => !closedStatuses.includes(p.status) && macroPhase(p.status) === "PRINTING",
  );
  const closed = projects.filter((p) => closedStatuses.includes(p.status));

  const columns: { title: string; hint: string; items: ProjectVM[] }[] = [
    { title: "In Modellazione", hint: "Dialogo col Progettista", items: modeling },
    { title: "In Stampa", hint: "Dialogo col Maker", items: printing },
    { title: "Conclusi", hint: "Archivio", items: closed },
  ];

  return (
    <div className="grid gap-5 md:grid-cols-3">
      {columns.map((col) => (
        <div
          key={col.title}
          className="rounded-xl border p-4"
          style={{ background: "var(--surface)", borderColor: "var(--border)" }}
        >
          <div className="mb-3">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-semibold">{col.title}</h2>
              <span
                className="rounded-full px-2 py-0.5 text-xs"
                style={{ background: "var(--surface-2)", color: "var(--muted)" }}
              >
                {col.items.length}
              </span>
            </div>
            <p className="text-xs" style={{ color: "var(--muted)" }}>
              {col.hint}
            </p>
          </div>
          <div className="space-y-3">
            {col.items.length === 0 ? (
              <p className="py-6 text-center text-xs" style={{ color: "var(--muted)" }}>
                Nessun progetto
              </p>
            ) : (
              col.items.map((p) => <ProjectCard key={p.id} project={p} />)
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
