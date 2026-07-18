"use client";

import { useState } from "react";
import {
  Check,
  ExternalLink,
  Loader2,
  RotateCcw,
  X,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/Button";
import type { CanalRevision } from "@/components/admin/SolicitudCard";

const TIPO_ICONO: Record<string, string> = {
  tiktok: "🎬",
  instagram: "📸",
  youtube: "▶️",
  spotify: "🎵",
  blog: "📝",
  facebook: "📘",
  twitter: "🐦",
  soundcloud: "🎧",
  radio: "📻",
  website: "🌐",
  eventos: "🎪",
  playlist: "🎶",
  otro: "🔗",
};

const ESTADO_CANAL: Record<
  string,
  { label: string; cls: string }
> = {
  pendiente: { label: "Pendiente", cls: "bg-warning/15 text-warning border-warning/30" },
  aprobado: { label: "Aprobado", cls: "bg-success/15 text-success border-success/30" },
  rechazado: { label: "Rechazado", cls: "bg-danger/15 text-danger border-danger/30" },
};

type Props = {
  canal: CanalRevision;
  solicitudPendiente: boolean;
  onAprobar: () => Promise<void>;
  onRechazar: (motivo: string) => Promise<void>;
  onRevertir: () => Promise<void>;
};

export function CanalRevisionCard({
  canal,
  solicitudPendiente,
  onAprobar,
  onRechazar,
  onRevertir,
}: Props) {
  const [busy, setBusy] = useState<"aprobar" | "rechazar" | "revertir" | null>(
    null,
  );
  const [showRechazar, setShowRechazar] = useState(false);
  const [motivo, setMotivo] = useState("");
  const [motivoError, setMotivoError] = useState<string | null>(null);

  const est = ESTADO_CANAL[canal.estado_revision] ?? ESTADO_CANAL.pendiente;

  async function handleAprobar() {
    setBusy("aprobar");
    try {
      await onAprobar();
    } finally {
      setBusy(null);
    }
  }

  async function handleRechazar() {
    if (motivo.trim().length < 10) {
      setMotivoError("El motivo debe tener al menos 10 caracteres.");
      return;
    }
    setBusy("rechazar");
    setMotivoError(null);
    try {
      await onRechazar(motivo.trim());
      setShowRechazar(false);
      setMotivo("");
    } finally {
      setBusy(null);
    }
  }

  async function handleRevertir() {
    setBusy("revertir");
    try {
      await onRevertir();
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="flex flex-col gap-3 rounded-lg border border-border bg-surface p-4 shadow-glow">
      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2 min-w-0">
          <span className="text-lg" aria-hidden>
            {TIPO_ICONO[canal.tipo] ?? "🔗"}
          </span>
          <div className="min-w-0">
            <p className="truncate text-sm font-semibold text-text">
              {canal.nombre}
            </p>
            <p className="text-xs capitalize text-text-muted">{canal.tipo}</p>
          </div>
        </div>
        <span
          className={cn(
            "inline-flex shrink-0 items-center rounded-full border px-2.5 py-0.5 text-xs font-medium",
            est.cls,
          )}
        >
          {est.label}
        </span>
      </div>

      {/* Redes sociales */}
      {canal.redes && canal.redes.length > 0 && (
        <div className="flex flex-col gap-1">
          {canal.redes.map((r, i) => (
            <a
              key={i}
              href={r.url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 text-xs text-primary-light hover:underline"
            >
              {r.es_principal ? "★" : " "}
              <span className="capitalize text-text-muted">{r.tipo}</span>
              <ExternalLink size={11} /> {r.url}
            </a>
          ))}
        </div>
      )}

      {/* Info row */}
      <div className="flex flex-wrap items-center gap-2 text-xs text-text-muted">
        {canal.audiencia_estimada != null && (
          <span className="rounded bg-surface-2 px-1.5 py-0.5">
            {canal.audiencia_estimada.toLocaleString("es")} seguidores
          </span>
        )}
        {canal.generos.length > 0 && (
          <span className="rounded bg-surface-2 px-1.5 py-0.5">
            {canal.generos.join(", ")}
          </span>
        )}
        <span className="rounded bg-surface-2 px-1.5 py-0.5">
          {canal.precio_creditos} crédito{canal.precio_creditos === 1 ? "" : "s"}
        </span>
      </div>

      {/* Descripción */}
      {canal.descripcion && (
        <p className="text-xs text-text-muted italic">&ldquo;{canal.descripcion}&rdquo;</p>
      )}

      {/* Descripción precio */}
      {canal.descripcion_precio && (
        <p className="text-xs text-text-muted">{canal.descripcion_precio}</p>
      )}

      {/* Motivo rechazo */}
      {canal.estado_revision === "rechazado" && canal.motivo_rechazo && (
        <div className="rounded-md border border-danger/30 bg-danger/10 p-2 text-xs text-danger">
          <span className="font-medium">Motivo:</span> {canal.motivo_rechazo}
        </div>
      )}

      {/* Acciones */}
      {solicitudPendiente && (
        <div className="flex gap-2 pt-1">
          {canal.estado_revision === "pendiente" && (
            <>
              <Button
                size="sm"
                variant="danger"
                onClick={() => setShowRechazar(true)}
                disabled={busy !== null}
              >
                <X size={14} /> Rechazar
              </Button>
              <Button
                size="sm"
                onClick={handleAprobar}
                loading={busy === "aprobar"}
              >
                <Check size={14} /> Aprobar
              </Button>
            </>
          )}
          {(canal.estado_revision === "aprobado" ||
            canal.estado_revision === "rechazado") && (
            <Button
              size="sm"
              variant="secondary"
              onClick={handleRevertir}
              loading={busy === "revertir"}
            >
              <RotateCcw size={14} /> Revertir
            </Button>
          )}
        </div>
      )}

      {/* Inline rejection form */}
      {showRechazar && (
        <div className="flex flex-col gap-2 rounded-md border border-border bg-surface-2 p-3">
          <label className="text-xs font-medium text-text-muted">
            Motivo del rechazo (mínimo 10 caracteres)
          </label>
          <textarea
            className="min-h-[60px] w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-text placeholder:text-text-muted/50 focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
            value={motivo}
            onChange={(e) => {
              setMotivo(e.target.value);
              setMotivoError(null);
            }}
            placeholder="Describe por qué no se aprueba este canal…"
          />
          {motivoError && (
            <p className="text-xs text-danger">{motivoError}</p>
          )}
          <div className="flex gap-2">
            <Button
              size="sm"
              variant="danger"
              onClick={handleRechazar}
              loading={busy === "rechazar"}
            >
              Confirmar rechazo
            </Button>
            <Button
              size="sm"
              variant="ghost"
              onClick={() => {
                setShowRechazar(false);
                setMotivo("");
                setMotivoError(null);
              }}
            >
              Cancelar
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
