"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/Button";
import { Alert } from "@/components/ui/Alert";
import { useDashboardUser } from "@/components/layout/DashboardProvider";

type UsuarioAdmin = {
  id: string;
  nombre_completo: string;
  correo: string;
  tipo: string;
  perfil_id: number;
  activo: boolean;
  created_at: string;
};
type Paginated = { items: UsuarioAdmin[]; total: number; page: number; page_size: number };
const PAGE_SIZE = 20;

export default function AdminUsuariosPage() {
  const router = useRouter();
  const user = useDashboardUser();
  const [data, setData] = useState<Paginated | null>(null);
  const [tipo, setTipo] = useState("");
  const [activo, setActivo] = useState("");
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);

  useEffect(() => {
    if (!user.es_admin) router.replace("/home");
  }, [user.es_admin, router]);

  const cargar = useCallback(async () => {
    setLoading(true);
    try {
      const qs = new URLSearchParams({ page: String(page), page_size: String(PAGE_SIZE) });
      if (tipo) qs.set("tipo", tipo);
      if (activo) qs.set("activo", activo);
      setData(await api.get<Paginated>(`/admin/usuarios?${qs.toString()}`));
      setError(null);
    } catch {
      setError("No se pudieron cargar los usuarios.");
    } finally {
      setLoading(false);
    }
  }, [tipo, activo, page]);

  useEffect(() => {
    void cargar();
  }, [cargar]);

  async function toggle(id: string) {
    setBusyId(id);
    try {
      await api.post(`/admin/usuarios/${id}/toggle-status`);
      await cargar();
    } finally {
      setBusyId(null);
    }
  }

  const totalPages = data ? Math.max(1, Math.ceil(data.total / PAGE_SIZE)) : 1;

  return (
    <div className="mx-auto flex w-full max-w-5xl flex-col gap-5">
      <header>
        <h1 className="text-2xl font-bold tracking-tight text-text">Usuarios</h1>
        <p className="mt-1 text-sm text-text-muted">Gestiona las cuentas de la plataforma.</p>
      </header>

      <div className="flex flex-wrap items-center gap-3">
        <select
          value={tipo}
          onChange={(e) => { setTipo(e.target.value); setPage(1); }}
          className="h-9 rounded-md border border-border bg-surface-2 px-3 text-sm text-text focus:outline-none focus:border-primary"
        >
          <option value="">Todos los tipos</option>
          <option value="artista">Artistas</option>
          <option value="curador">Curadores</option>
        </select>
        <select
          value={activo}
          onChange={(e) => { setActivo(e.target.value); setPage(1); }}
          className="h-9 rounded-md border border-border bg-surface-2 px-3 text-sm text-text focus:outline-none focus:border-primary"
        >
          <option value="">Activos e inactivos</option>
          <option value="true">Solo activos</option>
          <option value="false">Solo inactivos</option>
        </select>
      </div>

      {error && <Alert variant="error">{error}</Alert>}

      {loading ? (
        <div className="flex min-h-[30vh] items-center justify-center">
          <Loader2 className="animate-spin text-primary-light" size={28} />
        </div>
      ) : !data || data.items.length === 0 ? (
        <p className="rounded-lg border border-dashed border-border px-6 py-10 text-center text-sm text-text-muted">
          No hay usuarios con esos filtros.
        </p>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-border">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border bg-surface-2 text-left text-xs uppercase tracking-wide text-text-muted">
                <th className="px-4 py-2.5 font-medium">Usuario</th>
                <th className="px-4 py-2.5 font-medium">Tipo</th>
                <th className="px-4 py-2.5 font-medium">Estado</th>
                <th className="px-4 py-2.5 text-right font-medium">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((u) => {
                const esAdmin = u.perfil_id === 1;
                return (
                  <tr key={u.id} className="border-b border-border last:border-0">
                    <td className="px-4 py-3">
                      <p className="font-medium text-text">{u.nombre_completo}</p>
                      <p className="text-xs text-text-muted">{u.correo}</p>
                    </td>
                    <td className="px-4 py-3 text-text-muted">
                      {esAdmin ? "Admin" : u.tipo}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={cn(
                          "inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium",
                          u.activo ? "bg-success/15 text-success" : "bg-white/10 text-text-muted",
                        )}
                      >
                        {u.activo ? "Activo" : "Inactivo"}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex justify-end">
                        {!esAdmin && (
                          <Button
                            size="sm"
                            variant={u.activo ? "ghost" : "secondary"}
                            loading={busyId === u.id}
                            onClick={() => toggle(u.id)}
                          >
                            {u.activo ? "Desactivar" : "Activar"}
                          </Button>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {data && totalPages > 1 && (
        <div className="flex items-center justify-between text-sm text-text-muted">
          <span>{data.total} usuarios</span>
          <div className="flex items-center gap-2">
            <Button size="sm" variant="ghost" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
              Anterior
            </Button>
            <span>Página {page} de {totalPages}</span>
            <Button size="sm" variant="ghost" disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)}>
              Siguiente
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
