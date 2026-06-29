"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Pencil, Plus, Trash2 } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import { StepShell } from "@/components/onboarding/StepShell";
import {
  MedioForm,
  MEDIO_TYPES,
  type Genero,
  type MedioFormValues,
} from "@/components/onboarding/MedioForm";
import { Button } from "@/components/ui/Button";
import { Alert } from "@/components/ui/Alert";
import { useOnboardingProgress } from "@/hooks/useOnboardingProgress";

type Medio = {
  id: string;
  nombre: string;
  tipo: string;
  url: string | null;
  descripcion: string | null;
  audiencia_estimada: number | null;
  genero_ids: number[];
};

function tipoLabel(tipo: string) {
  return MEDIO_TYPES.find((t) => t.value === tipo)?.label ?? tipo;
}

export default function MediosPage() {
  const router = useRouter();
  const { nextHref, refresh, tipo: userTipo, loading } = useOnboardingProgress();
  const [generos, setGeneros] = useState<Genero[]>([]);
  const [medios, setMedios] = useState<Medio[]>([]);
  const [loadingData, setLoadingData] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState<Medio | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [removingId, setRemovingId] = useState<string | null>(null);
  const [navigating, setNavigating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Sólo curadores tienen este paso; un artista no debe llegar aquí.
  useEffect(() => {
    if (!loading && userTipo === "artista") {
      router.replace(nextHref("medios"));
    }
  }, [loading, userTipo, router, nextHref]);

  async function loadMedios() {
    try {
      setMedios(await api.get<Medio[]>("/onboarding/medios"));
    } catch (err) {
      if (!(err instanceof ApiError && err.status === 403)) {
        setError("No se pudieron cargar tus canales.");
      }
    } finally {
      setLoadingData(false);
    }
  }

  useEffect(() => {
    api
      .get<Genero[]>("/catalogos/generos")
      .then(setGeneros)
      .catch(() => setError("No se pudo cargar el catálogo de géneros."));
    void loadMedios();
  }, []);

  async function submitMedio(values: MedioFormValues) {
    setSubmitting(true);
    setError(null);
    try {
      if (editing) {
        await api.put(`/onboarding/medios/${editing.id}`, values);
      } else {
        await api.post("/onboarding/medios", values);
      }
      setShowForm(false);
      setEditing(null);
      await Promise.all([loadMedios(), refresh()]);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo guardar el canal.");
    } finally {
      setSubmitting(false);
    }
  }

  async function removeMedio(id: string) {
    setRemovingId(id);
    try {
      await api.del(`/onboarding/medios/${id}`);
      await Promise.all([loadMedios(), refresh()]);
    } catch {
      setError("No se pudo eliminar el canal.");
    } finally {
      setRemovingId(null);
    }
  }

  async function onContinue() {
    setNavigating(true);
    await refresh();
    router.push(nextHref("medios"));
  }

  function startEdit(medio: Medio) {
    setEditing(medio);
    setShowForm(true);
  }

  function startAdd() {
    setEditing(null);
    setShowForm(true);
  }

  return (
    <StepShell
      currentKey="medios"
      title="Tus medios y canales"
      description="Agrega los canales donde difundes música: playlists, blog, redes, radio… Indica qué géneros cubre cada uno."
      onContinue={onContinue}
      continueLoading={navigating}
    >
      {error && (
        <Alert variant="error" className="mb-4">
          {error}
        </Alert>
      )}

      <div className="flex flex-col gap-3">
        {loadingData ? (
          Array.from({ length: 2 }).map((_, i) => (
            <div key={i} className="credits-skeleton-shimmer h-20 rounded-md" />
          ))
        ) : medios.length === 0 ? (
          <p className="rounded-md border border-dashed border-border px-4 py-6 text-center text-sm text-text-muted">
            Aún no agregas canales. Agrega al menos uno para recibir campañas afines.
          </p>
        ) : (
          medios.map((m) => (
            <div
              key={m.id}
              className="flex items-start justify-between gap-3 rounded-md border border-border bg-surface-2 px-4 py-3"
            >
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <p className="truncate font-medium text-text">{m.nombre}</p>
                  <span className="rounded-full bg-primary/15 px-2 py-0.5 text-xs text-primary-light">
                    {tipoLabel(m.tipo)}
                  </span>
                </div>
                {m.descripcion && (
                  <p className="mt-0.5 truncate text-sm text-text-muted">
                    {m.descripcion}
                  </p>
                )}
                <p className="mt-1 text-xs text-text-muted">
                  {m.genero_ids.length} género
                  {m.genero_ids.length === 1 ? "" : "s"}
                  {m.audiencia_estimada != null &&
                    ` · ${m.audiencia_estimada.toLocaleString("es")} de audiencia`}
                </p>
              </div>
              <div className="flex shrink-0 gap-1">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => startEdit(m)}
                  aria-label={`Editar ${m.nombre}`}
                >
                  <Pencil size={15} />
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => removeMedio(m.id)}
                  loading={removingId === m.id}
                  aria-label={`Eliminar ${m.nombre}`}
                >
                  <Trash2 size={15} />
                </Button>
              </div>
            </div>
          ))
        )}
      </div>

      {showForm ? (
        <div className="mt-5">
          <MedioForm
            generos={generos}
            initial={editing ?? undefined}
            submitting={submitting}
            submitLabel={editing ? "Guardar cambios" : "Agregar canal"}
            onSubmit={submitMedio}
            onCancel={() => {
              setShowForm(false);
              setEditing(null);
            }}
          />
        </div>
      ) : (
        <Button variant="secondary" className="mt-5" onClick={startAdd}>
          <Plus size={16} />
          Agregar canal
        </Button>
      )}
    </StepShell>
  );
}
