import type {
  MaterialType,
  PrinterStatus,
  PrinterTechnology,
  ProjectPhase,
  ProjectStatus,
  QCStatus,
} from "@prisma/client";

// View-models consumed by the dashboards. Kept separate from Prisma rows so the
// UI is decoupled from the persistence layer.

export interface ProjectVM {
  id: string;
  title: string;
  category: string;
  status: ProjectStatus;
  clientName: string;
  designerName: string | null;
  makerName: string | null;
  designPrice: number | null;
  printPrice: number | null;
  material: MaterialType | null;
  requiredX: number | null;
  requiredY: number | null;
  requiredZ: number | null;
  qcStatus: QCStatus;
  qcDueAt: string | null;
  renderUrl: string | null;
  qcPhotoUrls: string[];
  updatedAt: string;
}

export interface PrinterVM {
  id: string;
  name: string;
  technology: PrinterTechnology;
  buildX: number;
  buildY: number;
  buildZ: number;
  materials: MaterialType[];
  status: PrinterStatus;
  octoprintConnected: boolean;
}

// What a maker sees in "Find Jobs": technical metadata only, never the source.
export interface JobVM {
  id: string;
  title: string;
  category: string;
  material: MaterialType | null;
  requiredX: number;
  requiredY: number;
  requiredZ: number;
  volumeCm3: number | null;
  printPrice: number | null;
}

/** Maps a granular project status to the client Kanban macro-phase. */
export function macroPhase(status: ProjectStatus): ProjectPhase {
  const modeling: ProjectStatus[] = [
    "DRAFT",
    "MODELING",
    "MODEL_REVIEW",
    "MODEL_APPROVED",
  ] as ProjectStatus[];
  return modeling.includes(status) ? ("MODELING" as ProjectPhase) : ("PRINTING" as ProjectPhase);
}
