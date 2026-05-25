import { DashboardShell } from "@/components/DashboardShell";
import { KanbanBoard } from "@/components/KanbanBoard";
import { getClientProjects } from "@/lib/repositories/projects";

export default async function ClientDashboard() {
  const projects = await getClientProjects();

  return (
    <DashboardShell
      active="client"
      title="I miei progetti"
      subtitle="Timeline dei lavori attivi, divisi per macro-fase."
    >
      <KanbanBoard projects={projects} />
    </DashboardShell>
  );
}
