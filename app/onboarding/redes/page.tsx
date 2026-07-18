"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Plus } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import { StepShell } from "@/components/onboarding/StepShell";
import {
  RED_PLATFORMS,
  RedSocialRow,
  platformMeta,
} from "@/components/onboarding/RedSocialRow";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Alert } from "@/components/ui/Alert";
import { cn } from "@/lib/utils";
import { useOnboardingProgress } from "@/hooks/useOnboardingProgress";

type Red = { id: string; tipo: string; url: string };

export default function RedesPage() {
  const router = useRouter();
  const { nextHref, refresh, tipo: userTipo, loading } = useOnboardingProgress();
  const [redes, setRedes] = useState<Red[]>([]);
  const [tipo, setTipo] = useState(RED_PLATFORMS[0].value);
  const [url, setUrl] = useState("");
  const [loadingList, setLoadingList] = useState(true);
  const [adding, setAdding] = useState(false);
  const [removingId, setRemovingId] = useState<string | null>(null);
  const [navigating, setNavigating] = useState(false);

  // Curadores no usan este paso — sus redes son de sus canales
  useEffect(() => {
    if (!loading && userTipo === "curador") {
      router.replace("/onboarding/medios");
    }
  }, [loading, userTipo, router]);
  const [error, setError] = useState<string | null>(null);

  async function loadRedes() {
    try {
      setRedes(await api.get<Red[]>("/onboarding/redes"));
    } catch {
      setError("No se pudieron cargar tus redes.");
    } finally {
      setLoadingList(false);
    }
  }

  useEffect(() => {
    void loadRedes();
  }, []);

  async function addRed(e: React.FormEvent) {
    e.preventDefault();
    if (url.trim().length < 3) {
      setError("Ingresa una URL válida.");
      return;
    }
    setAdding(true);
    setError(null);
    try {
      await api.post("/onboarding/redes", { tipo, url: url.trim() });
      setUrl("");
      await Promise.all([loadRedes(), refresh()]);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo agregar.");
    } finally {
      setAdding(false);
    }
  }

  async function removeRed(id: string) {
    setRemovingId(id);
    try {
      await api.del(`/onboarding/redes/${id}`);
      await Promise.all([loadRedes(), refresh()]);
    } catch {
      setError("No se pudo eliminar la red.");
    } finally {
      setRemovingId(null);
    }
  }

  async function onContinue() {
    setNavigating(true);
    await refresh();
    router.push(nextHref("redes"));
  }

  const placeholder = platformMeta(tipo).placeholder;

  return (
    <StepShell
      currentKey="redes"
      title="Conecta tus redes sociales"
      description="Agrega los enlaces de tus plataformas. Este paso es opcional, pero ayuda a que te conozcan mejor."
      onContinue={onContinue}
      continueLoading={navigating}
    >
      {error && (
        <Alert variant="error" className="mb-4">
          {error}
        </Alert>
      )}

      <form onSubmit={addRed} className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-end">
        <div className="flex flex-col gap-1.5 sm:w-48">
          <label htmlFor="red-tipo" className="text-sm font-medium text-text-muted">
            Plataforma
          </label>
          <select
            id="red-tipo"
            value={tipo}
            onChange={(e) => setTipo(e.target.value)}
            className={cn(
              "h-[42px] w-full rounded-md border border-border bg-surface-2 px-3 text-sm text-text",
              "transition-all focus:outline-none focus:border-primary focus:ring-2 focus:ring-[var(--accent-glow)]",
            )}
          >
            {RED_PLATFORMS.map((p) => (
              <option key={p.value} value={p.value} className="text-text">
                {p.label}
              </option>
            ))}
          </select>
        </div>
        <div className="flex-1">
          <Input
            label="URL"
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder={placeholder}
          />
        </div>
        <Button type="submit" loading={adding} className="sm:mb-0">
          <Plus size={16} />
          Agregar
        </Button>
      </form>

      <div className="flex flex-col gap-2">
        {loadingList ? (
          Array.from({ length: 2 }).map((_, i) => (
            <div key={i} className="credits-skeleton-shimmer h-16 rounded-md" />
          ))
        ) : redes.length === 0 ? (
          <p className="rounded-md border border-dashed border-border px-4 py-6 text-center text-sm text-text-muted">
            Aún no agregas redes. Puedes hacerlo ahora o más tarde desde tu perfil.
          </p>
        ) : (
          redes.map((r) => (
            <RedSocialRow
              key={r.id}
              tipo={r.tipo}
              url={r.url}
              onRemove={() => removeRed(r.id)}
              removing={removingId === r.id}
            />
          ))
        )}
      </div>
    </StepShell>
  );
}
