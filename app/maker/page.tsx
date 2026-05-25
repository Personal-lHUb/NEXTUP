import { DashboardShell, Card } from "@/components/DashboardShell";
import { PrinterCard } from "@/components/PrinterCard";
import { JobBoard } from "@/components/JobBoard";
import { getMakerPrinters } from "@/lib/repositories/printers";
import { getOpenJobs } from "@/lib/repositories/projects";

export default async function MakerDashboard() {
  const [printers, jobs] = await Promise.all([getMakerPrinters(), getOpenJobs()]);

  return (
    <DashboardShell
      active="maker"
      title="Dashboard Maker"
      subtitle="Gestisci le tue stampanti e trova lavori compatibili col tuo hardware."
    >
      <section className="mb-10">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold">Gestione stampanti</h2>
          <button
            className="rounded-lg px-3 py-1.5 text-sm font-semibold text-white"
            style={{ background: "var(--accent)" }}
          >
            + Aggiungi stampante
          </button>
        </div>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {printers.map((p) => (
            <PrinterCard key={p.id} printer={p} />
          ))}
        </div>
      </section>

      <section>
        <h2 className="mb-4 text-lg font-semibold">Trova lavori</h2>
        <Card>
          <JobBoard printers={printers} jobs={jobs} />
        </Card>
      </section>
    </DashboardShell>
  );
}
