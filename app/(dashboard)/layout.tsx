import { redirect } from "next/navigation";
import { serverApi } from "@/lib/server-api";
import {
  DashboardProvider,
  type DashboardUser,
} from "@/components/layout/DashboardProvider";
import { Sidebar } from "@/components/layout/Sidebar";
import { Header } from "@/components/layout/Header";

/**
 * Layout de las rutas protegidas. Server Component: valida la sesión contra el
 * backend (`/auth/me`) reenviando la cookie. Si no hay sesión válida, redirige
 * a `/login`. El usuario obtenido se inyecta al árbol cliente vía contexto.
 *
 * El shell visual (Sidebar T2, Header T3) se monta sobre este layout.
 */
export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  let user: DashboardUser | null = null;
  try {
    user = await serverApi.get<DashboardUser>("/auth/me");
  } catch {
    user = null;
  }

  if (!user) {
    redirect("/login");
  }

  return (
    <DashboardProvider user={user}>
      <div className="flex min-h-screen bg-base text-text">
        <Sidebar />
        <div className="flex min-w-0 flex-1 flex-col">
          <Header />
          <main className="flex-1 px-4 py-6 sm:px-6 lg:px-8">{children}</main>
        </div>
      </div>
    </DashboardProvider>
  );
}
