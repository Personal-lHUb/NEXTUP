import Link from "next/link";
import type { ProjectVM } from "@/lib/types";
import { formatEUR } from "@/lib/money";
import { StatusBadge } from "./StatusBadge";

export function ProjectCard({ project }: { project: ProjectVM }) {
  const total =
    (project.designPrice ?? 0) + (project.printPrice ?? 0) || null;

  return (
    <Link
      href={`/client/projects/${project.id}` as const}
      className="block rounded-lg border p-4 transition-colors hover:border-[var(--accent)]"
      style={{ background: "var(--surface-2)", borderColor: "var(--border)" }}
    >
      <div className="mb-2 flex items-start justify-between gap-2">
        <h3 className="text-sm font-semibold leading-snug">{project.title}</h3>
        <StatusBadge status={project.status} />
      </div>
      <div className="space-y-1 text-xs" style={{ color: "var(--muted)" }}>
        {project.designerName && <p>Designer: {project.designerName}</p>}
        {project.makerName && <p>Maker: {project.makerName}</p>}
        {project.material && <p>Materiale: {project.material}</p>}
        {total != null && (
          <p className="pt-1 font-medium" style={{ color: "var(--text)" }}>
            {formatEUR(total)}
          </p>
        )}
      </div>
    </Link>
  );
}
