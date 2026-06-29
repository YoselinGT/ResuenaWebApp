"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import { GenreChip } from "@/components/onboarding/GenreChip";
import { StepShell } from "@/components/onboarding/StepShell";
import { Alert } from "@/components/ui/Alert";
import { useOnboardingProgress } from "@/hooks/useOnboardingProgress";

type Idioma = { codigo: string; nombre: string };

export default function IdiomasPage() {
  const router = useRouter();
  const { nextHref, refresh } = useOnboardingProgress();
  const [idiomas, setIdiomas] = useState<Idioma[]>([]);
  const [selected, setSelected] = useState<string[]>([]);
  const [loadingCat, setLoadingCat] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .get<Idioma[]>("/catalogos/idiomas")
      .then(setIdiomas)
      .catch(() => setError("No se pudo cargar el catálogo de idiomas."))
      .finally(() => setLoadingCat(false));
  }, []);

  function toggle(codigo: string) {
    setSelected((prev) =>
      prev.includes(codigo)
        ? prev.filter((c) => c !== codigo)
        : [...prev, codigo],
    );
  }

  async function onContinue() {
    if (selected.length === 0) return;
    setSaving(true);
    setError(null);
    try {
      await api.put("/onboarding/idiomas", { codigos: selected });
      await refresh();
      router.push(nextHref("idiomas"));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo guardar.");
      setSaving(false);
    }
  }

  return (
    <StepShell
      currentKey="idiomas"
      title="¿En qué idiomas creas o consumes música?"
      description="Selecciona los idiomas de tu contenido. Mínimo uno."
      onContinue={onContinue}
      continueDisabled={selected.length === 0}
      continueLoading={saving}
    >
      {error && (
        <Alert variant="error" className="mb-4">
          {error}
        </Alert>
      )}

      {loadingCat ? (
        <div className="flex flex-wrap gap-2">
          {Array.from({ length: 8 }).map((_, i) => (
            <div
              key={i}
              className="credits-skeleton-shimmer h-9 w-28 rounded-full"
            />
          ))}
        </div>
      ) : (
        <>
          <div className="flex flex-wrap gap-2">
            {idiomas.map((idioma) => (
              <GenreChip
                key={idioma.codigo}
                label={idioma.nombre}
                selected={selected.includes(idioma.codigo)}
                onToggle={() => toggle(idioma.codigo)}
              />
            ))}
          </div>
          <p className="mt-4 text-xs text-text-muted">
            {selected.length} seleccionado{selected.length === 1 ? "" : "s"}
          </p>
        </>
      )}
    </StepShell>
  );
}
