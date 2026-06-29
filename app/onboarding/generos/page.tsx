"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import { GenreChip } from "@/components/onboarding/GenreChip";
import { StepShell } from "@/components/onboarding/StepShell";
import { Alert } from "@/components/ui/Alert";
import { useOnboardingProgress } from "@/hooks/useOnboardingProgress";

type Genero = { id: number; nombre: string };

export default function GenerosPage() {
  const router = useRouter();
  const { nextHref, refresh } = useOnboardingProgress();
  const [generos, setGeneros] = useState<Genero[]>([]);
  const [selected, setSelected] = useState<number[]>([]);
  const [loadingCat, setLoadingCat] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .get<Genero[]>("/catalogos/generos")
      .then(setGeneros)
      .catch(() => setError("No se pudo cargar el catálogo de géneros."))
      .finally(() => setLoadingCat(false));
  }, []);

  function toggle(id: number) {
    setSelected((prev) =>
      prev.includes(id) ? prev.filter((g) => g !== id) : [...prev, id],
    );
  }

  async function onContinue() {
    if (selected.length === 0) return;
    setSaving(true);
    setError(null);
    try {
      await api.put("/onboarding/generos", { genero_ids: selected });
      await refresh();
      router.push(nextHref("generos"));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo guardar.");
      setSaving(false);
    }
  }

  return (
    <StepShell
      currentKey="generos"
      title="¿Qué géneros te representan?"
      description="Elige los géneros con los que más conectas. Los usamos para emparejar campañas con curadores afines. Mínimo uno."
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
          {Array.from({ length: 12 }).map((_, i) => (
            <div
              key={i}
              className="credits-skeleton-shimmer h-9 w-24 rounded-full"
            />
          ))}
        </div>
      ) : (
        <>
          <div className="flex flex-wrap gap-2">
            {generos.map((g) => (
              <GenreChip
                key={g.id}
                label={g.nombre}
                selected={selected.includes(g.id)}
                onToggle={() => toggle(g.id)}
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
