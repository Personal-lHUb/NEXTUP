import { DashboardShell } from "@/components/DashboardShell";
import { KanbanBoard } from "@/components/KanbanBoard";
import { getClientProjects } from "@/lib/repositories/projects";
import { requireRole } from "@/lib/auth/guards";

export default async function ClientDashboard() {
  const user = await requireRole("CLIENT");
  const projects = await getClientProjects();

  return (
    <DashboardShell
      active="client"
      title="I miei progetti"
      subtitle="Timeline dei lavori attivi, divisi per macro-fase."
      user={user}
    >
      <KanbanBoard projects={projects} />
    </DashboardShell>
  );
}
