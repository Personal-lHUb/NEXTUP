import { DashboardShell, Card } from "@/components/DashboardShell";
import { StatusBadge } from "@/components/StatusBadge";
import { getClientProjects } from "@/lib/repositories/projects";
import { formatEUR } from "@/lib/money";

export default async function DesignerDashboard() {
  const projects = await getClientProjects();
  const assignments = projects.filter((p) => p.designerName);

  return (
    <DashboardShell
      active="designer"
      title="Dashboard Progettista"
      subtitle="Carica i modelli sui server blindati e gestisci le commesse di modellazione."
    >
      <Card className="mb-6">
        <h2 className="mb-1 text-sm font-semibold">Caricamento file sorgente</h2>
        <p className="mb-3 text-xs" style={{ color: "var(--muted)" }}>
          STL / OBJ / 3MF / STEP. I file restano blindati: i Maker non possono scaricarli, ricevono
          solo i metadati tecnici (ingombro, volume) e la stampa via streaming protetto.
        </p>
        <div
          className="grid place-items-center rounded-lg border border-dashed py-10 text-sm"
          style={{ borderColor: "var(--border)", color: "var(--muted)" }}
        >
          Trascina qui un file o clicca per caricare (upload protetto)
        </div>
      </Card>

      <h2 className="mb-3 text-lg font-semibold">Le mie commesse</h2>
      <div className="space-y-3">
        {assignments.map((p) => (
          <div
            key={p.id}
            className="flex items-center justify-between rounded-lg border p-4"
            style={{ background: "var(--surface)", borderColor: "var(--border)" }}
          >
            <div>
              <h3 className="text-sm font-semibold">{p.title}</h3>
              <p className="text-xs" style={{ color: "var(--muted)" }}>
                Cliente: {p.clientName}
              </p>
            </div>
            <div className="flex items-center gap-4">
              {p.designPrice != null && (
                <span className="text-sm font-medium">{formatEUR(p.designPrice)}</span>
              )}
              <StatusBadge status={p.status} />
            </div>
          </div>
        ))}
      </div>
    </DashboardShell>
  );
}
