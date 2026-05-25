import { notFound } from "next/navigation";
import { DashboardShell, Card } from "@/components/DashboardShell";
import { StatusBadge } from "@/components/StatusBadge";
import { ModelViewer } from "@/components/ModelViewer";
import { QCApproval } from "@/components/QCApproval";
import { getProjectById } from "@/lib/repositories/projects";
import { computeOrderBreakdown, formatEUR } from "@/lib/money";

export default async function ProjectDetail({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const project = await getProjectById(id);
  if (!project) notFound();

  const breakdown =
    project.designPrice != null && project.printPrice != null
      ? computeOrderBreakdown({
          designPrice: project.designPrice,
          printPrice: project.printPrice,
          shippingCarrierCost: 7.5,
        })
      : null;

  const showModelReview = project.status === "MODEL_REVIEW";
  const showQC = project.status === "QC_PENDING";

  return (
    <DashboardShell active="client" title={project.title} subtitle={`Categoria: ${project.category}`}>
      <div className="mb-4">
        <StatusBadge status={project.status} />
      </div>

      <div className="grid gap-5 lg:grid-cols-3">
        <div className="space-y-5 lg:col-span-2">
          {showModelReview && (
            <Card>
              <h2 className="mb-1 text-sm font-semibold">Approva il render del Progettista</h2>
              <p className="mb-3 text-xs" style={{ color: "var(--muted)" }}>
                Viewer protetto con watermark dinamico. Il file sorgente non è scaricabile.
              </p>
              <ModelViewer renderUrl={project.renderUrl} watermarkLabel={project.clientName} />
              <div className="mt-4 flex gap-3">
                <button
                  className="rounded-lg px-4 py-2 text-sm font-semibold text-white"
                  style={{ background: "var(--accent-2)" }}
                >
                  Approva render
                </button>
                <button
                  className="rounded-lg border px-4 py-2 text-sm font-semibold"
                  style={{ borderColor: "var(--border)" }}
                >
                  Richiedi revisione
                </button>
              </div>
            </Card>
          )}

          {showQC && (
            <Card>
              <h2 className="mb-1 text-sm font-semibold">Controllo qualità pre-spedizione</h2>
              <p className="mb-3 text-xs" style={{ color: "var(--muted)" }}>
                Il Maker ha caricato le foto HD del piatto di stampa. Approva per generare l'etichetta.
              </p>
              <QCApproval
                projectId={project.id}
                photoUrls={project.qcPhotoUrls}
                dueAt={project.qcDueAt}
              />
            </Card>
          )}

          {!showModelReview && !showQC && (
            <Card>
              <h2 className="mb-1 text-sm font-semibold">Stato del progetto</h2>
              <p className="text-xs" style={{ color: "var(--muted)" }}>
                Nessuna azione richiesta in questo momento. Ti avviseremo quando il Progettista o il
                Maker avranno bisogno di una tua approvazione.
              </p>
            </Card>
          )}
        </div>

        <div className="space-y-5">
          <Card>
            <h2 className="mb-3 text-sm font-semibold">Team</h2>
            <dl className="space-y-2 text-xs">
              <Row label="Cliente" value={project.clientName} />
              <Row label="Progettista" value={project.designerName ?? "Da assegnare"} />
              <Row label="Maker" value={project.makerName ?? "Da assegnare"} />
              <Row label="Materiale" value={project.material ?? "—"} />
              <Row
                label="Ingombro"
                value={
                  project.requiredX
                    ? `${project.requiredX}×${project.requiredY}×${project.requiredZ} mm`
                    : "—"
                }
              />
            </dl>
          </Card>

          {breakdown && (
            <Card>
              <h2 className="mb-3 text-sm font-semibold">Riepilogo pagamento (escrow)</h2>
              <dl className="space-y-2 text-xs">
                <Row label="Progettazione" value={formatEUR(breakdown.designPrice)} />
                <Row label="Stampa" value={formatEUR(breakdown.printPrice)} />
                <Row label="Spedizione" value={formatEUR(breakdown.shippingCost)} />
                <div className="my-2 border-t" style={{ borderColor: "var(--border)" }} />
                <Row label="Totale (congelato)" value={formatEUR(breakdown.clientTotal)} strong />
                <p className="pt-2 text-[11px]" style={{ color: "var(--muted)" }}>
                  Commissione piattaforma: {formatEUR(breakdown.platformFee)} (
                  {(breakdown.takeRateBps / 100).toFixed(1)}%). I fondi vengono sbloccati a lavoro
                  approvato.
                </p>
              </dl>
            </Card>
          )}
        </div>
      </div>
    </DashboardShell>
  );
}

function Row({ label, value, strong }: { label: string; value: string; strong?: boolean }) {
  return (
    <div className="flex items-center justify-between">
      <dt style={{ color: "var(--muted)" }}>{label}</dt>
      <dd style={{ color: "var(--text)", fontWeight: strong ? 600 : 400 }}>{value}</dd>
    </div>
  );
}
