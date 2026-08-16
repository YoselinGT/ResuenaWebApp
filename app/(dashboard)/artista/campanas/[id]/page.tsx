"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, Loader2, Music, Play, Pause } from "lucide-react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Alert } from "@/components/ui/Alert";

type CampanaMedio = {
  id: string;
  medio_id: string;
  curador_id: string;
  estado: string;
  precio_snapshot: number;
  creditos_retenidos: number;
  fecha_limite: string | null;
};

type Campana = {
  id: string;
  artista_id: string;
  titulo: string;
  descripcion: string | null;
  url_audio: string | null;
  url_imagen: string | null;
  url_material: string | null;
  genero_id: number;
  estado: string;
  creditos_usados: number;
  created_at: string;
  updated_at: string;
  medios: CampanaMedio[];
};

const ESTADO_CONFIG: Record<
  string,
  { label: string; cls: string }
> = {
  borrador: { label: "Borrador", cls: "bg-warning/15 text-warning" },
  enviada: { label: "Enviada", cls: "bg-primary/15 text-primary-light" },
  en_revision: { label: "En revisión", cls: "bg-info/15 text-info" },
  completada: { label: "Completada", cls: "bg-success/15 text-success" },
  cancelada: { label: "Cancelada", cls: "bg-text-muted/15 text-text-muted" },
};

const ESTADO_MEDIO: Record<
  string,
  { label: string; cls: string }
> = {
  pendiente: { label: "Pendiente", cls: "bg-warning/15 text-warning" },
  aceptada: { label: "Aceptada", cls: "bg-success/15 text-success" },
  rechazada: { label: "Rechazada", cls: "bg-danger/15 text-danger" },
  entregada: { label: "Entregada", cls: "bg-primary/15 text-primary-light" },
  expirada: { label: "Expirada", cls: "bg-text-muted/15 text-text-muted" },
};

export default function CampanaDetallePage() {
  const params = useParams();
  const [campana, setCampana] = useState<Campana | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [playing, setPlaying] = useState(false);

  useEffect(() => {
    if (!params.id) return;

    api
      .get<Campana>(`/campanas/${params.id}`)
      .then(setCampana)
      .catch(() => setError("No se pudo cargar la campaña."))
      .finally(() => setLoading(false));
  }, [params.id]);

  if (loading) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center">
        <Loader2 className="animate-spin text-primary-light" size={32} />
      </div>
    );
  }

  if (error || !campana) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-8">
        <Alert variant="error">{error || "Campaña no encontrada."}</Alert>
      </div>
    );
  }

  const estado = ESTADO_CONFIG[campana.estado] || ESTADO_CONFIG.borrador;

  return (
    <div className="mx-auto flex w-full max-w-3xl flex-col gap-6 px-4 py-8">
      <Link
        href="/artista/campanas"
        className="inline-flex items-center gap-2 text-sm text-text-muted hover:text-text"
      >
        <ArrowLeft size={16} />
        Volver a campañas
      </Link>

      <header>
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-text">
              {campana.titulo}
            </h1>
            {campana.descripcion && (
              <p className="mt-2 text-sm text-text-muted">
                {campana.descripcion}
              </p>
            )}
          </div>
          <span className={`rounded-full px-3 py-1 text-sm font-medium ${estado.cls}`}>
            {estado.label}
          </span>
        </div>
      </header>

      {/* Imagen y audio */}
      <div className="grid gap-4 sm:grid-cols-2">
        {campana.url_imagen && (
          <div className="overflow-hidden rounded-lg">
            <img
              src={campana.url_imagen}
              alt={campana.titulo}
              className="h-48 w-full object-cover sm:h-64"
            />
          </div>
        )}

        {campana.url_audio && (
          <div className="flex flex-col justify-center gap-4 rounded-lg border border-border bg-surface p-4">
            <div className="flex items-center gap-3">
              <button
                onClick={() => setPlaying(!playing)}
                className="flex h-12 w-12 items-center justify-center rounded-full bg-primary text-white transition-colors hover:bg-primary/90"
              >
                {playing ? <Pause size={20} /> : <Play size={20} />}
              </button>
              <div>
                <p className="font-medium text-text">Audio de la campaña</p>
                <p className="text-xs text-text-muted">MP3/WAV</p>
              </div>
            </div>
            {/* TODO: Audio player real */}
          </div>
        )}
      </div>

      {/* Material adicional */}
      {campana.url_material && (
        <div className="rounded-lg border border-border bg-surface p-4">
          <p className="text-sm font-medium text-text">Material adicional</p>
          <a
            href={campana.url_material}
            target="_blank"
            rel="noopener noreferrer"
            className="mt-1 text-sm text-primary hover:underline"
          >
            Descargar ZIP
          </a>
        </div>
      )}

      {/* Curadores vinculados */}
      <div>
        <h2 className="mb-4 text-lg font-semibold text-text">
          Curadores vinculados
        </h2>
        {campana.medios.length === 0 ? (
          <p className="text-sm text-text-muted">
            No hay curadores vinculados aún.
          </p>
        ) : (
          <div className="space-y-3">
            {campana.medios.map((medio) => {
              const estadoMedio =
                ESTADO_MEDIO[medio.estado] || ESTADO_MEDIO.pendiente;

              return (
                <div
                  key={medio.id}
                  className="flex items-center justify-between rounded-lg border border-border bg-surface p-4"
                >
                  <div>
                    <p className="text-sm font-medium text-text">
                      Curador: {medio.curador_id}
                    </p>
                    <p className="text-xs text-text-muted">
                      {medio.precio_snapshot} crédito(s) ·{" "}
                      {medio.creditos_retenidos} retenido(s)
                    </p>
                  </div>
                  <span
                    className={`rounded-full px-2.5 py-1 text-xs font-medium ${estadoMedio.cls}`}
                  >
                    {estadoMedio.label}
                  </span>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Información adicional */}
      <div className="rounded-lg border border-border bg-surface p-4">
        <div className="grid gap-2 text-sm">
          <div className="flex justify-between">
            <span className="text-text-muted">Créditos usados</span>
            <span className="font-medium text-text">
              {campana.creditos_usados}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-text-muted">Creada</span>
            <span className="text-text">
              {new Date(campana.created_at).toLocaleString()}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-text-muted">Última actualización</span>
            <span className="text-text">
              {new Date(campana.updated_at).toLocaleString()}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
