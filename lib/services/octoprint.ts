// OctoPrint integration. The platform pushes sliced G-code directly to the
// maker's printer and starts the job; the maker never receives a file they can
// keep. Klipper/Moonraker would be analogous (different endpoints).

export interface OctoPrintTarget {
  url: string; // e.g. http://octopi.local
  apiKey: string;
}

/**
 * Uploads G-code to OctoPrint's local storage and immediately starts printing.
 * The file is marked for selection + print in one call.
 */
export async function uploadAndPrint(
  target: OctoPrintTarget,
  gcode: Buffer,
  filename: string,
): Promise<{ ok: boolean; status: number }> {
  const form = new FormData();
  form.append("file", new Blob([new Uint8Array(gcode)], { type: "text/plain" }), filename);
  form.append("select", "true");
  form.append("print", "true");

  const res = await fetch(`${target.url.replace(/\/$/, "")}/api/files/local`, {
    method: "POST",
    headers: { "X-Api-Key": target.apiKey },
    body: form,
  });

  return { ok: res.ok, status: res.status };
}
