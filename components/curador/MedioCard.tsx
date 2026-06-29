"use client";

import { useState } from "react";
import {
  CalendarDays,
  FileText,
  Globe,
  Instagram,
  Link2,
  ListMusic,
  Music2,
  Pencil,
  Radio,
  Twitter,
  Youtube,
  Facebook,
  type LucideIcon,
} from "lucide-react";
import { api, ApiError } from "@/lib/api";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/Button";

export type MedioStats = {
  recibidas: number;
  aceptadas: number;
  entregadas: number;
  tasa_aceptacion: number;
};

export type Medio = {
  id: string;
  nombre: string;
  tipo: string;
  url: string | null;
  descripcion: string | null;
  audiencia_estimada: number | null;
  activo: boolean;
  genero_ids: number[];
  stats: MedioStats;
};

const TIPO_ICON: Record<string, LucideIcon> = {
  playlist: ListMusic,
  blog: FileText,
  instagram: Instagram,
  tiktok: Music2,
  youtube: Youtube,
  facebook: Facebook,
  twitter: Twitter,
  radio: Radio,
  website: Globe,
  eventos: CalendarDays,
  otro: Link2,
};

type Props = {
  medio: Medio;
  generosMap: Record<number, string>;
  onEdit: (medio: Medio) => void;
  onChanged: (medio: Medio) => void;
};

export function MedioCard({ medio, generosMap, onEdit, onChanged }: Props) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const Icon = TIPO_ICON[medio.tipo] ?? Link2;

  async function toggle() {
    setBusy(true);
    setError(null);
    try {
      const actualizado = await api.post<Medio>(
        `/curador/medios/${medio.id}/toggle-activo`,
      );
      onChanged(actualizado);
    } catch (err) {
      setError(
        err instanceof ApiError && err.status === 409
          ? "Tienes campañas activas en este medio."
          : err instanceof ApiError
            ? err.message
            : "No se pudo cambiar el estado.",
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <article
      className={cn(
        "flex flex-col gap-3 rounded-lg border bg-surface p-5 transition-opacity",
        medio.activo ? "border-border" : "border-border opacity-60",
      )}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2.5 min-w-0">
          <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md bg-primary/15 text-primary-light">
            <Icon size={18} />
          </span>
          <div className="min-w-0">
            <p className="truncate font-medium text-text">{medio.nombre}</p>
            {medio.url && (
              <a
                href={medio.url}
                target="_blank"
                rel="noopener noreferrer"
                className="block truncate text-xs text-text-muted hover:text-primary-light hover:underline"
              >
                {medio.url}
              </a>
            )}
          </div>
        </div>
        <Button variant="ghost" size="sm" onClick={() => onEdit(medio)} aria-label="Editar medio">
          <Pencil size={15} />
        </Button>
      </div>

      {medio.genero_ids.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {medio.genero_ids.map((id) => (
            <span
              key={id}
              className="rounded-full bg-surface-2 px-2.5 py-0.5 text-xs text-text-muted"
            >
              {generosMap[id] ?? `#${id}`}
            </span>
          ))}
        </div>
      )}

      <div className="flex items-center gap-4 text-xs text-text-muted">
        <span>
          <strong className="text-text">{medio.stats.recibidas}</strong> recibidas
        </span>
        <span>
          <strong className="text-text">{medio.stats.aceptadas}</strong> aceptadas
        </span>
      </div>

      {error && <p className="text-xs text-danger">{error}</p>}

      <div className="mt-1 flex items-center justify-between border-t border-border pt-3">
        <span className="text-xs text-text-muted">
          {medio.activo ? "Activo" : "Inactivo"}
        </span>
        <button
          type="button"
          onClick={toggle}
          disabled={busy}
          role="switch"
          aria-checked={medio.activo}
          aria-label={medio.activo ? "Desactivar medio" : "Activar medio"}
          className={cn(
            "relative h-6 w-11 rounded-full transition-colors disabled:opacity-50",
            medio.activo ? "bg-primary" : "bg-border",
          )}
        >
          <span
            className={cn(
              "absolute top-0.5 h-5 w-5 rounded-full bg-text transition-transform",
              medio.activo ? "translate-x-[22px]" : "translate-x-0.5",
            )}
          />
        </button>
      </div>
    </article>
  );
}
