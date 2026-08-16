"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Loader2, Plus, Music } from "lucide-react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Alert } from "@/components/ui/Alert";

type Campana = {
  id: string;
  titulo: string;
  estado: string;
  genero_id: number;
  creditos_usados: number;
  url_imagen: string | null;
  created_at: string;
  updated_at: string;
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

export default function CampanasPage() {
  const [campanas, setCampanas] = useState<Campana[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .get<{ items: Campana[] }>("/campanas")
      .then((res) => setCampanas(res.items))
      .catch(() => setError("No se pudieron cargar las campañas."))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center">
        <Loader2 className="animate-spin text-primary-light" size={32} />
      </div>
    );
  }

  return (
    <div className="mx-auto flex w-full max-w-4xl flex-col gap-6 px-4 py-8">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-text">
            Mis campañas
          </h1>
          <p className="mt-1 text-sm text-text-muted">
            Gestiona tus campañas musicales.
          </p>
        </div>
        <Link href="/artista/campanas/nueva">
          <Button>
            <Plus size={16} />
            Nueva campaña
          </Button>
        </Link>
      </header>

      {error && <Alert variant="error">{error}</Alert>}

      {campanas.length === 0 ? (
        <div className="flex flex-col items-center justify-center gap-4 rounded-lg border border-dashed border-border px-6 py-12 text-center">
          <Music size={48} className="text-text-muted" />
          <div>
            <p className="font-medium text-text">No tienes campañas</p>
            <p className="text-sm text-text-muted">
              Crea tu primera campaña para empezar a promocionar tu música.
            </p>
          </div>
          <Link href="/artista/campanas/nueva">
            <Button>
              <Plus size={16} />
              Crear campaña
            </Button>
          </Link>
        </div>
      ) : (
        <div className="grid gap-4">
          {campanas.map((campana) => {
            const estado = ESTADO_CONFIG[campana.estado] || ESTADO_CONFIG.borrador;

            return (
              <Link
                key={campana.id}
                href={`/artista/campanas/${campana.id}`}
                className="flex items-center gap-4 rounded-lg border border-border bg-surface p-4 transition-colors hover:bg-surface-2"
              >
                {campana.url_imagen ? (
                  <img
                    src={campana.url_imagen}
                    alt={campana.titulo}
                    className="h-16 w-16 rounded-lg object-cover"
                  />
                ) : (
                  <div className="flex h-16 w-16 items-center justify-center rounded-lg bg-surface-2">
                    <Music size={24} className="text-text-muted" />
                  </div>
                )}

                <div className="flex-1 min-w-0">
                  <p className="truncate font-medium text-text">
                    {campana.titulo}
                  </p>
                  <p className="mt-1 text-xs text-text-muted">
                    {campana.creditos_usados} crédito(s) ·{" "}
                    {new Date(campana.created_at).toLocaleDateString()}
                  </p>
                </div>

                <span
                  className={`rounded-full px-2.5 py-1 text-xs font-medium ${estado.cls}`}
                >
                  {estado.label}
                </span>
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}
