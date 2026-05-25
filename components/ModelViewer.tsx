"use client";

import { useEffect, useState } from "react";

/**
 * Protected render viewer. In production this renders a server-streamed render
 * (or a low-poly proxy mesh) — never the source STL/OBJ — with a dynamic
 * watermark tied to the viewer's identity and timestamp to deter screen-capture
 * leaks. Here it shows the watermark behaviour over a placeholder image.
 */
export function ModelViewer({
  renderUrl,
  watermarkLabel,
}: {
  renderUrl: string | null;
  watermarkLabel: string;
}) {
  const [stamp, setStamp] = useState("");

  useEffect(() => {
    const update = () => setStamp(new Date().toLocaleString("it-IT"));
    update();
    const id = setInterval(update, 1000);
    return () => clearInterval(id);
  }, []);

  const tiles = Array.from({ length: 24 });

  return (
    <div
      className="relative aspect-video w-full overflow-hidden rounded-lg border"
      style={{ borderColor: "var(--border)", background: "var(--surface-2)" }}
    >
      {renderUrl ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={renderUrl} alt="Render protetto" className="h-full w-full object-cover opacity-90" />
      ) : (
        <div className="grid h-full place-items-center text-sm" style={{ color: "var(--muted)" }}>
          Render protetto non disponibile
        </div>
      )}

      {/* Dynamic watermark overlay */}
      <div className="pointer-events-none absolute inset-0 grid grid-cols-4 gap-6 p-4 opacity-30">
        {tiles.map((_, i) => (
          <span
            key={i}
            className="select-none text-[10px] font-semibold uppercase tracking-wider"
            style={{ transform: "rotate(-24deg)", color: "white" }}
          >
            {watermarkLabel} · {stamp}
          </span>
        ))}
      </div>
    </div>
  );
}
