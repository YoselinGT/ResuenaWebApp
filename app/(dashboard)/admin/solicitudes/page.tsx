"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Check, Loader2, X } from "lucide-react";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/Button";
import { Alert } from "@/components/ui/Alert";
import { useDashboardUser } from "@/components/layout/DashboardProvider";
import { EstadoBadge, type Solicitud } from "@/components/admin/SolicitudCard";
import { RechazarModal } from "@/components/admin/RechazarModal";

type Paginated = { items: Solicitud[]; total: number; page: number; page_size: number };
const PAGE_SIZE = 20;
const ESTADOS = ["", "pendiente", "aprobada", "rechazada"] as const;

export default function AdminSolicitudesPage() {
  const router = useRouter();
  const user = useDashboardUser();
  const [data, setData] = useState<Paginated | null>(null);
  const [estado, setEstado] = useState("");
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [rechazar, setRechazar] = useState<Solicitud | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);

  useEffect(() => {
    if (!user.es_admin) router.replace("/home");
  }, [user.es_admin, router]);

  const cargar = useCallback(async () => {
    setLoading(true);
    try {
      const qs = new URLSearchParams({ page: String(page), page_size: String(PAGE_SIZE) });
      if (estado) qs.set("estado", estado);
      setData(await api.get<Paginated>(`/admin/solicitudes?${qs.toString()}`));
      setError(null);
    } catch {
      setError("No se pudieron cargar las solicitudes.");
    } finally {
      setLoading(false);
    }
  }, [estado, page]);

  useEffect(() => {
    void cargar();
  }, [cargar]);

  async function aprobar(id: string) {
    setBusyId(id);
    try {
      await api.post(`/admin/solicitudes/${id}/aprobar`);
      await cargar();
    } finally {
      setBusyId(null);
    }
  }

  const totalPages = data ? Math.max(1, Math.ceil(data.total / PAGE_SIZE)) : 1;

  return (
    <div className="mx-auto flex w-full max-w-5xl flex-col gap-5">
      <header>
        <h1 className="text-2xl font-bold tracking-tight text-text">Solicitudes de curador</h1>
        <p className="mt-1 text-sm text-text-muted">Revisa, aprueba o rechaza las solicitudes.</p>
      </header>

      <div className="flex items-center gap-2">
        {ESTADOS.map((e) => (
          <button
            key={e || "todos"}
            onClick={() => {
              setEstado(e);
              setPage(1);
            }}
            className={cn(
              "rounded-full px-3 py-1 text-sm transition-colors",
              estado === e ? "bg-primary text-text" : "bg-surface-2 text-text-muted hover:text-text",
            )}
          >
            {e === "" ? "Todas" : e.charAt(0).toUpperCase() + e.slice(1)}
          </button>
        ))}
      </div>

      {error && <Alert variant="error">{error}</Alert>}

      {loading ? (
        <div className="flex min-h-[30vh] items-center justify-center">
          <Loader2 className="animate-spin text-primary-light" size={28} />
        </div>
      ) : !data || data.items.length === 0 ? (
        <p className="rounded-lg border border-dashed border-border px-6 py-10 text-center text-sm text-text-muted">
          No hay solicitudes{estado && ` ${estado}s`}.
        </p>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-border">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border bg-surface-2 text-left text-xs uppercase tracking-wide text-text-muted">
                <th className="px-4 py-2.5 font-medium">Curador</th>
                <th className="px-4 py-2.5 font-medium">Tipo</th>
                <th className="px-4 py-2.5 font-medium">Estado</th>
                <th className="px-4 py-2.5 text-right font-medium">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((s) => (
                <tr key={s.id} className="border-b border-border last:border-0">
                  <td className="px-4 py-3">
                    <Link href={`/admin/solicitudes/${s.id}`} className="hover:underline">
                      <p className="font-medium text-text">{s.nombre_completo}</p>
                      <p className="text-xs text-text-muted">{s.correo}</p>
                    </Link>
                  </td>
                  <td className="px-4 py-3 text-text-muted">{s.tipo_profesional ?? "—"}</td>
                  <td className="px-4 py-3"><EstadoBadge estado={s.estado} /></td>
                  <td className="px-4 py-3">
                    <div className="flex justify-end gap-1.5">
                      {s.estado === "pendiente" && (
                        <>
                          <Button
                            size="sm"
                            loading={busyId === s.id}
                            onClick={() => aprobar(s.id)}
                          >
                            <Check size={14} /> Aprobar
                          </Button>
                          <Button
                            size="sm"
                            variant="danger"
                            disabled={busyId === s.id}
                            onClick={() => setRechazar(s)}
                          >
                            <X size={14} /> Rechazar
                          </Button>
                        </>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {data && totalPages > 1 && (
        <div className="flex items-center justify-between text-sm text-text-muted">
          <span>{data.total} solicitudes</span>
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

      {rechazar && (
        <RechazarModal
          solicitudId={rechazar.id}
          nombre={rechazar.nombre_completo}
          onClose={() => setRechazar(null)}
          onRejected={() => {
            setRechazar(null);
            void cargar();
          }}
        />
      )}
    </div>
  );
}
