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

type CanalRed = { tipo: string; url: string; es_principal: boolean };

type CanalAdmin = {
  id: string;
  nombre: string;
  tipo: string;
  descripcion: string | null;
  audiencia_estimada: number | null;
  precio_creditos: number;
  descripcion_precio: string | null;
  estado_revision: string;
  motivo_rechazo: string | null;
  revisado_at: string | null;
  curador_id: string;
  curador_nombre: string;
  curador_correo: string;
  generos: string[];
  redes: CanalRed[];
  created_at: string;
};

type Paginated = { items: CanalAdmin[]; total: number; page: number; page_size: number };

const PAGE_SIZE = 20;
const ESTADOS = ["", "pendiente", "aprobado", "rechazado"] as const;

const ESTADO_CONFIG: Record<string, { label: string; cls: string }> = {
  pendiente: { label: "Pendiente", cls: "bg-warning/15 text-warning" },
  aprobado: { label: "Aprobado", cls: "bg-success/15 text-success" },
  rechazado: { label: "Rechazado", cls: "bg-danger/15 text-danger" },
};

function EstadoBadge({ estado }: { estado: string }) {
  const e = ESTADO_CONFIG[estado] ?? { label: estado, cls: "bg-white/10 text-text-muted" };
  return (
    <span className={cn("inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium", e.cls)}>
      {e.label}
    </span>
  );
}

export default function AdminCanalesPage() {
  const router = useRouter();
  const user = useDashboardUser();
  const [data, setData] = useState<Paginated | null>(null);
  const [estado, setEstado] = useState("");
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
      if (estado) qs.set("estado_revision", estado);
      setData(await api.get<Paginated>(`/admin/solicitudes/canales?${qs.toString()}`));
      setError(null);
    } catch {
      setError("No se pudieron cargar los canales.");
    } finally {
      setLoading(false);
    }
  }, [estado, page]);

  useEffect(() => {
    void cargar();
  }, [cargar]);

  async function aprobar(canalId: string) {
    setBusyId(canalId);
    try {
      await api.post(`/admin/solicitudes/canales/${canalId}/aprobar`);
      await cargar();
    } finally {
      setBusyId(null);
    }
  }

  async function rechazar(canalId: string, motivo: string) {
    setBusyId(canalId);
    try {
      await api.post(`/admin/solicitudes/canales/${canalId}/rechazar`, { motivo });
      await cargar();
    } finally {
      setBusyId(null);
    }
  }

  async function revertir(canalId: string) {
    setBusyId(canalId);
    try {
      await api.post(`/admin/solicitudes/canales/${canalId}/pendiente`);
      await cargar();
    } finally {
      setBusyId(null);
    }
  }

  const totalPages = data ? Math.max(1, Math.ceil(data.total / PAGE_SIZE)) : 1;

  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-5">
      <header>
        <h1 className="text-2xl font-bold tracking-tight text-text">Canales de curadores</h1>
        <p className="mt-1 text-sm text-text-muted">Revisa, aprueba o rechaza los canales individuales.</p>
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
            {e === "" ? "Todos" : e.charAt(0).toUpperCase() + e.slice(1)}
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
          No hay canales{estado && ` ${estado}s`}.
        </p>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-border">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border bg-surface-2 text-left text-xs uppercase tracking-wide text-text-muted">
                <th className="px-4 py-2.5 font-medium">Canal</th>
                <th className="px-4 py-2.5 font-medium">Tipo</th>
                <th className="px-4 py-2.5 font-medium">Curador</th>
                <th className="px-4 py-2.5 font-medium">Estado</th>
                <th className="px-4 py-2.5 text-right font-medium">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((c) => (
                <tr key={c.id} className="border-b border-border last:border-0">
                  <td className="px-4 py-3">
                    <Link href={`/admin/solicitudes/${c.id}`} className="hover:underline">
                      <p className="font-medium text-text">{c.nombre}</p>
                      <p className="text-xs text-text-muted">
                        {c.generos.length > 0 ? c.generos.join(", ") : "Sin géneros"}
                      </p>
                    </Link>
                  </td>
                  <td className="px-4 py-3 text-text-muted capitalize">{c.tipo}</td>
                  <td className="px-4 py-3">
                    <p className="text-text">{c.curador_nombre}</p>
                    <p className="text-xs text-text-muted">{c.curador_correo}</p>
                  </td>
                  <td className="px-4 py-3">
                    <EstadoBadge estado={c.estado_revision} />
                    {c.estado_revision === "rechazado" && c.motivo_rechazo && (
                      <p className="mt-1 text-xs text-danger truncate max-w-[200px]" title={c.motivo_rechazo}>
                        {c.motivo_rechazo}
                      </p>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex justify-end gap-1.5">
                      {c.estado_revision === "pendiente" && (
                        <>
                          <Button
                            size="sm"
                            loading={busyId === c.id}
                            onClick={() => aprobar(c.id)}
                          >
                            <Check size={14} /> Aprobar
                          </Button>
                          <Button
                            size="sm"
                            variant="danger"
                            disabled={busyId === c.id}
                            onClick={() => {
                              const motivo = prompt("Motivo del rechazo (mínimo 10 caracteres):");
                              if (motivo && motivo.length >= 10) rechazar(c.id, motivo);
                            }}
                          >
                            <X size={14} /> Rechazar
                          </Button>
                        </>
                      )}
                      {(c.estado_revision === "aprobado" || c.estado_revision === "rechazado") && (
                        <Button
                          size="sm"
                          variant="ghost"
                          loading={busyId === c.id}
                          onClick={() => revertir(c.id)}
                        >
                          Revertir
                        </Button>
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
          <span>{data.total} canales</span>
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
