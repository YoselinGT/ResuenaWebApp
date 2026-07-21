"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, Check, Loader2, X } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/Button";
import { Alert } from "@/components/ui/Alert";
import { useDashboardUser } from "@/components/layout/DashboardProvider";

type CanalRed = { tipo: string; url: string; es_principal: boolean };

type CanalDetalle = {
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

const ESTADO_CONFIG: Record<string, { label: string; cls: string }> = {
  pendiente: { label: "Pendiente", cls: "bg-warning/15 text-warning" },
  aprobado: { label: "Aprobado", cls: "bg-success/15 text-success" },
  rechazado: { label: "Rechazado", cls: "bg-danger/15 text-danger" },
};

const TIPO_ICONO: Record<string, string> = {
  playlist: "🎶",
  blog: "📝",
  instagram: "📸",
  tiktok: "🎬",
  youtube: "▶️",
  facebook: "📘",
  twitter: "🐦",
  radio: "📻",
  website: "🌐",
  eventos: "🎪",
  otro: "🔗",
};

export default function AdminCanalDetallePage() {
  const params = useParams();
  const router = useRouter();
  const user = useDashboardUser();
  const [canal, setCanal] = useState<CanalDetalle | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!user.es_admin) router.replace("/home");
  }, [user.es_admin, router]);

  const cargar = useCallback(async () => {
    try {
      setCanal(await api.get<CanalDetalle>(`/admin/solicitudes/canales/${params.id}`));
      setError(null);
    } catch {
      setError("No se pudo cargar el canal.");
    } finally {
      setLoading(false);
    }
  }, [params.id]);

  useEffect(() => {
    void cargar();
  }, [cargar]);

  async function aprobar() {
    setBusy(true);
    try {
      await api.post(`/admin/solicitudes/canales/${params.id}/aprobar`);
      await cargar();
    } finally {
      setBusy(false);
    }
  }

  async function rechazar() {
    const motivo = prompt("Motivo del rechazo (mínimo 10 caracteres):");
    if (!motivo || motivo.length < 10) return;
    setBusy(true);
    try {
      await api.post(`/admin/solicitudes/canales/${params.id}/rechazar`, { motivo });
      await cargar();
    } finally {
      setBusy(false);
    }
  }

  async function revertir() {
    setBusy(true);
    try {
      await api.post(`/admin/solicitudes/canales/${params.id}/pendiente`);
      await cargar();
    } finally {
      setBusy(false);
    }
  }

  if (loading) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center">
        <Loader2 className="animate-spin text-primary-light" size={28} />
      </div>
    );
  }

  if (error || !canal) {
    return (
      <div className="mx-auto max-w-2xl">
        <Alert variant="error">{error ?? "Canal no encontrado."}</Alert>
      </div>
    );
  }

  const estado = ESTADO_CONFIG[canal.estado_revision] ?? ESTADO_CONFIG.pendiente;

  return (
    <div className="mx-auto flex w-full max-w-3xl flex-col gap-6">
      <Link
        href="/admin/solicitudes"
        className="inline-flex items-center gap-1.5 text-sm text-text-muted hover:text-text"
      >
        <ArrowLeft size={16} /> Volver a canales
      </Link>

      {/* Header del canal */}
      <div className="rounded-lg border border-border bg-surface p-6">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-center gap-3">
            <span className="text-3xl">{TIPO_ICONO[canal.tipo] ?? "🔗"}</span>
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-text">{canal.nombre}</h1>
              <p className="text-sm text-text-muted capitalize">{canal.tipo}</p>
            </div>
          </div>
          <span className={cn("rounded-full px-3 py-1 text-sm font-medium", estado.cls)}>
            {estado.label}
          </span>
        </div>

        {canal.descripcion && (
          <p className="mt-4 text-sm text-text-muted">{canal.descripcion}</p>
        )}

        {canal.estado_revision === "rechazado" && canal.motivo_rechazo && (
          <div className="mt-4 rounded-lg border border-danger/30 bg-danger/10 p-3">
            <p className="text-sm font-medium text-danger">Motivo del rechazo:</p>
            <p className="mt-1 text-sm text-danger/80">{canal.motivo_rechazo}</p>
          </div>
        )}
      </div>

      {/* Info del curador */}
      <div className="rounded-lg border border-border bg-surface p-6">
        <h2 className="text-lg font-semibold text-text mb-3">Curador</h2>
        <div className="grid gap-2 text-sm">
          <div className="flex justify-between">
            <span className="text-text-muted">Nombre</span>
            <span className="text-text font-medium">{canal.curador_nombre}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-text-muted">Correo</span>
            <span className="text-text">{canal.curador_correo}</span>
          </div>
        </div>
      </div>

      {/* Redes sociales — sección principal de revisión */}
      <div className="rounded-lg border-2 border-primary/30 bg-surface p-6">
        <h2 className="text-lg font-semibold text-text mb-1">Redes sociales del canal</h2>
        <p className="text-xs text-text-muted mb-4">Revisa cada red social para decidir si aprobar o rechazar este canal.</p>
        
        {canal.redes.length === 0 ? (
          <p className="text-sm text-text-muted">Este canal no tiene redes sociales registradas.</p>
        ) : (
          <div className="flex flex-col gap-3">
            {canal.redes.map((r, i) => (
              <div
                key={i}
                className={cn(
                  "flex items-center justify-between rounded-lg border p-4",
                  r.es_principal
                    ? "border-warning/40 bg-warning/5"
                    : "border-border bg-surface-2",
                )}
              >
                <div className="flex items-center gap-3 min-w-0">
                  <span className="text-2xl">{TIPO_ICONO[r.tipo] ?? "🔗"}</span>
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <p className="font-medium text-text capitalize">{r.tipo}</p>
                      {r.es_principal && (
                        <span className="rounded-full bg-warning/20 px-2 py-0.5 text-[10px] font-semibold text-warning">
                          ★ Principal
                        </span>
                      )}
                    </div>
                    <a
                      href={r.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-sm text-primary-light hover:underline break-all"
                    >
                      {r.url}
                    </a>
                  </div>
                </div>
                <a
                  href={r.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="shrink-0 rounded-lg border border-border px-3 py-1.5 text-xs text-text-muted hover:text-text hover:bg-surface-2 transition-colors"
                >
                  Abrir ↗
                </a>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Info del canal */}
      <div className="rounded-lg border border-border bg-surface p-6">
        <h2 className="text-lg font-semibold text-text mb-3">Detalles del canal</h2>
        <div className="grid gap-2 text-sm">
          {canal.audiencia_estimada && (
            <div className="flex justify-between">
              <span className="text-text-muted">Audiencia estimada</span>
              <span className="text-text">{canal.audiencia_estimada.toLocaleString()}</span>
            </div>
          )}
          <div className="flex justify-between">
            <span className="text-text-muted">Precio por campaña</span>
            <span className="text-text font-medium">{canal.precio_creditos} crédito(s)</span>
          </div>
          {canal.descripcion_precio && (
            <div className="flex justify-between">
              <span className="text-text-muted">Descripción del precio</span>
              <span className="text-text">{canal.descripcion_precio}</span>
            </div>
          )}
          {canal.generos.length > 0 && (
            <div className="flex justify-between">
              <span className="text-text-muted">Géneros</span>
              <span className="text-text">{canal.generos.join(", ")}</span>
            </div>
          )}
          <div className="flex justify-between">
            <span className="text-text-muted">Creado</span>
            <span className="text-text">{new Date(canal.created_at).toLocaleString()}</span>
          </div>
          {canal.revisado_at && (
            <div className="flex justify-between">
              <span className="text-text-muted">Revisado</span>
              <span className="text-text">{new Date(canal.revisado_at).toLocaleString()}</span>
            </div>
          )}
        </div>
      </div>

      {/* Acciones */}
      <div className="flex gap-3">
        {canal.estado_revision === "pendiente" && (
          <>
            <Button onClick={aprobar} loading={busy}>
              <Check size={16} /> Aprobar canal
            </Button>
            <Button variant="danger" onClick={rechazar} disabled={busy}>
              <X size={16} /> Rechazar canal
            </Button>
          </>
        )}
        {(canal.estado_revision === "aprobado" || canal.estado_revision === "rechazado") && (
          <Button variant="ghost" onClick={revertir} loading={busy}>
            Revertir a pendiente
          </Button>
        )}
      </div>
    </div>
  );
}
