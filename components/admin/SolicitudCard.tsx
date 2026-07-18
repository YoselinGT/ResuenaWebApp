"use client";

import { CalendarDays, Mail } from "lucide-react";
import { cn } from "@/lib/utils";

export type Red = { tipo: string; url: string };

export type CanalRed = { tipo: string; url: string; es_principal: boolean };

export type CanalRevision = {
  id: string;
  nombre: string;
  tipo: string;
  url: string | null;
  descripcion: string | null;
  audiencia_estimada: number | null;
  precio_creditos: number;
  descripcion_precio: string | null;
  generos: string[];
  redes: CanalRed[];
  estado_revision: string;
  motivo_rechazo: string | null;
  revisado_at: string | null;
};

export type Solicitud = {
  id: string;
  usuario_id: string;
  nombre_completo: string;
  correo: string;
  estado: string;
  tipo_profesional: string | null;
  notas_revision: string | null;
  revisor_id: string | null;
  created_at: string;
  redes?: Red[];
  canales?: CanalRevision[];
};

const ESTADO: Record<string, { label: string; cls: string }> = {
  pendiente: { label: "Pendiente", cls: "bg-warning/15 text-warning" },
  aprobada: { label: "Aprobada", cls: "bg-success/15 text-success" },
  rechazada: { label: "Rechazada", cls: "bg-danger/15 text-danger" },
};

export function EstadoBadge({ estado }: { estado: string }) {
  const e = ESTADO[estado] ?? { label: estado, cls: "bg-white/10 text-text-muted" };
  return (
    <span className={cn("inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium", e.cls)}>
      {e.label}
    </span>
  );
}

export function SolicitudCard({ solicitud }: { solicitud: Solicitud }) {
  const s = solicitud;
  return (
    <div className="flex flex-col gap-4 rounded-lg border border-border bg-surface p-6 shadow-glow">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h2 className="truncate text-lg font-bold text-text">{s.nombre_completo}</h2>
          <p className="flex items-center gap-1.5 text-sm text-text-muted">
            <Mail size={14} /> {s.correo}
          </p>
        </div>
        <EstadoBadge estado={s.estado} />
      </div>

      <dl className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <div>
          <dt className="text-xs text-text-muted">Tipo de profesional</dt>
          <dd className="text-sm text-text">{s.tipo_profesional ?? "—"}</dd>
        </div>
        <div>
          <dt className="text-xs text-text-muted">Solicitado</dt>
          <dd className="flex items-center gap-1.5 text-sm text-text">
            <CalendarDays size={14} />
            {new Date(s.created_at).toLocaleDateString("es")}
          </dd>
        </div>
      </dl>

      {s.redes && s.redes.length > 0 && (
        <div>
          <p className="mb-1.5 text-xs text-text-muted">Redes sociales</p>
          <ul className="flex flex-col gap-1">
            {s.redes.map((r) => (
              <li key={r.tipo + r.url} className="text-sm">
                <span className="capitalize text-text-muted">{r.tipo}: </span>
                <a
                  href={r.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary-light hover:underline"
                >
                  {r.url}
                </a>
              </li>
            ))}
          </ul>
        </div>
      )}

      {s.estado === "rechazada" && s.notas_revision && (
        <div className="rounded-md border border-danger/30 bg-danger/10 p-3 text-sm text-danger">
          <span className="font-medium">Motivo del rechazo:</span> {s.notas_revision}
        </div>
      )}
    </div>
  );
}
