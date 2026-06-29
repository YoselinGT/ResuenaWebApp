"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { Search } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import { GenreChip } from "@/components/onboarding/GenreChip";
import { StepShell } from "@/components/onboarding/StepShell";
import { Input } from "@/components/ui/Input";
import { Alert } from "@/components/ui/Alert";
import { useOnboardingProgress } from "@/hooks/useOnboardingProgress";

type Region = { codigo: string; nombre: string };

export default function RegionesPage() {
  const router = useRouter();
  const { nextHref, refresh } = useOnboardingProgress();
  const [regiones, setRegiones] = useState<Region[]>([]);
  const [selected, setSelected] = useState<string[]>([]);
  const [query, setQuery] = useState("");
  const [loadingCat, setLoadingCat] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .get<Region[]>("/catalogos/regiones")
      .then(setRegiones)
      .catch(() => setError("No se pudo cargar el catálogo de regiones."))
      .finally(() => setLoadingCat(false));
  }, []);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return regiones;
    return regiones.filter((r) => r.nombre.toLowerCase().includes(q));
  }, [regiones, query]);

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
      await api.put("/onboarding/regiones", { codigos: selected });
      await refresh();
      router.push(nextHref("regiones"));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo guardar.");
      setSaving(false);
    }
  }

  return (
    <StepShell
      currentKey="regiones"
      title="¿Qué regiones te interesan?"
      description="Elige los países o regiones donde quieres tener presencia. Mínimo uno."
      onContinue={onContinue}
      continueDisabled={selected.length === 0}
      continueLoading={saving}
    >
      {error && (
        <Alert variant="error" className="mb-4">
          {error}
        </Alert>
      )}

      <div className="mb-4 max-w-sm">
        <Input
          aria-label="Buscar región"
          placeholder="Buscar país o región…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          leftIcon={<Search size={16} />}
        />
      </div>

      {loadingCat ? (
        <div className="flex flex-wrap gap-2">
          {Array.from({ length: 14 }).map((_, i) => (
            <div
              key={i}
              className="credits-skeleton-shimmer h-9 w-28 rounded-full"
            />
          ))}
        </div>
      ) : filtered.length === 0 ? (
        <p className="text-sm text-text-muted">
          Sin resultados para “{query}”.
        </p>
      ) : (
        <div className="flex flex-wrap gap-2">
          {filtered.map((r) => (
            <GenreChip
              key={r.codigo}
              label={r.nombre}
              selected={selected.includes(r.codigo)}
              onToggle={() => toggle(r.codigo)}
            />
          ))}
        </div>
      )}

      <p className="mt-4 text-xs text-text-muted">
        {selected.length} seleccionada{selected.length === 1 ? "" : "s"}
      </p>
    </StepShell>
  );
}
