import { USE_MOCK_DATA } from "../constants";
import { MOCK_JOBS, MOCK_PROJECTS } from "../mock-data";
import type { JobVM, ProjectVM } from "../types";

// Repositories return view-models. When USE_MOCK_DATA is true (default) they
// serve in-memory demo data; otherwise they query Postgres via Prisma.

export async function getClientProjects(): Promise<ProjectVM[]> {
  if (USE_MOCK_DATA) return MOCK_PROJECTS;

  const { prisma } = await import("../prisma");
  const rows = await prisma.project.findMany({
    include: {
      client: true,
      designer: true,
      maker: true,
      renders: { take: 1, orderBy: { createdAt: "desc" } },
      qcPhotos: true,
    },
    orderBy: { updatedAt: "desc" },
  });
  return rows.map(toProjectVM);
}

export async function getProjectById(id: string): Promise<ProjectVM | null> {
  if (USE_MOCK_DATA) return MOCK_PROJECTS.find((p) => p.id === id) ?? null;

  const { prisma } = await import("../prisma");
  const row = await prisma.project.findUnique({
    where: { id },
    include: {
      client: true,
      designer: true,
      maker: true,
      renders: { take: 1, orderBy: { createdAt: "desc" } },
      qcPhotos: true,
    },
  });
  return row ? toProjectVM(row) : null;
}

export async function getOpenJobs(): Promise<JobVM[]> {
  if (USE_MOCK_DATA) return MOCK_JOBS;

  const { prisma } = await import("../prisma");
  const rows = await prisma.project.findMany({
    where: { status: "MATCHING" },
    include: { designFiles: { take: 1 } },
  });
  return rows.map((p): JobVM => {
    const design = p.designFiles[0];
    return {
      id: p.id,
      title: p.title,
      category: p.category,
      material: p.material,
      requiredX: p.requiredX ?? design?.boundingBoxX ?? 0,
      requiredY: p.requiredY ?? design?.boundingBoxY ?? 0,
      requiredZ: p.requiredZ ?? design?.boundingBoxZ ?? 0,
      volumeCm3: design?.volumeCm3 ?? null,
      printPrice: p.printPrice ? Number(p.printPrice) : null,
    };
  });
}

// ─────────────────────────── mappers ─────────────────────────

// `row` is a Prisma Project with the includes above. Typed loosely to avoid a
// hard compile-time dependency on the generated client in this scaffold.
function toProjectVM(row: any): ProjectVM {
  return {
    id: row.id,
    title: row.title,
    category: row.category,
    status: row.status,
    clientName: row.client?.name ?? "—",
    designerName: row.designer?.name ?? null,
    makerName: row.maker?.name ?? null,
    designPrice: row.designPrice != null ? Number(row.designPrice) : null,
    printPrice: row.printPrice != null ? Number(row.printPrice) : null,
    material: row.material ?? null,
    requiredX: row.requiredX ?? null,
    requiredY: row.requiredY ?? null,
    requiredZ: row.requiredZ ?? null,
    qcStatus: row.qcStatus,
    qcDueAt: row.qcDueAt ? new Date(row.qcDueAt).toISOString() : null,
    renderUrl: row.renders?.[0]?.url ?? null,
    qcPhotoUrls: (row.qcPhotos ?? []).map((q: any) => q.url),
    updatedAt: new Date(row.updatedAt).toISOString(),
  };
}
