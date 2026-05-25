import type { MaterialType, PrinterTechnology } from "@prisma/client";

export interface PrinterCapability {
  buildX: number;
  buildY: number;
  buildZ: number;
  technology: PrinterTechnology;
  materials: MaterialType[];
}

export interface JobRequirement {
  requiredX: number;
  requiredY: number;
  requiredZ: number;
  material?: MaterialType | null;
}

/**
 * A printer can fulfil a job if the part fits inside the build volume (trying
 * the two flat-rotation orientations on the X/Y plane) and the required
 * material is supported. Matching is capability-based, never geographic.
 */
export function isCompatible(printer: PrinterCapability, job: JobRequirement): boolean {
  const fits = fitsInVolume(printer, job);
  if (!fits) return false;

  if (job.material && !printer.materials.includes(job.material)) return false;

  return true;
}

function fitsInVolume(printer: PrinterCapability, job: JobRequirement): boolean {
  const { requiredX: rx, requiredY: ry, requiredZ: rz } = job;
  if (rz > printer.buildZ) return false;

  // Footprint must fit in either orientation on the bed.
  const orientationA = rx <= printer.buildX && ry <= printer.buildY;
  const orientationB = ry <= printer.buildX && rx <= printer.buildY;
  return orientationA || orientationB;
}

/** Filters a list of jobs down to those a given printer can handle. */
export function compatibleJobs<T extends JobRequirement>(
  printer: PrinterCapability,
  jobs: T[],
): T[] {
  return jobs.filter((job) => isCompatible(printer, job));
}
