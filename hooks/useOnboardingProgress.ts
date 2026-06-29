"use client";

/**
 * Estado del wizard de onboarding: tipo de usuario, progreso por paso y
 * helpers de navegación. Se expone vía contexto (un solo fetch para layout +
 * páginas). Consume `GET /auth/me` y `GET /onboarding/progreso`.
 */

import {
  createContext,
  createElement,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import { useRouter } from "next/navigation";
import { api, ApiError } from "@/lib/api";

export type StepKey = "generos" | "idiomas" | "regiones" | "medios" | "redes";

export type OnboardingProgress = {
  generos: boolean;
  idiomas: boolean;
  regiones: boolean;
  redes: boolean;
  medios: boolean;
  preferencias: boolean;
};

export type Step = {
  key: StepKey;
  label: string;
  href: string;
  done: boolean;
  index: number; // 1-based
};

type Tipo = "artista" | "curador";

const STEP_META: Record<StepKey, { label: string; href: string }> = {
  generos: { label: "Géneros", href: "/onboarding/generos" },
  idiomas: { label: "Idiomas", href: "/onboarding/idiomas" },
  regiones: { label: "Regiones", href: "/onboarding/regiones" },
  medios: { label: "Tus medios", href: "/onboarding/medios" },
  redes: { label: "Redes sociales", href: "/onboarding/redes" },
};

const ORDER: Record<Tipo, StepKey[]> = {
  artista: ["generos", "idiomas", "regiones", "redes"],
  curador: ["generos", "idiomas", "regiones", "medios", "redes"],
};

const EMPTY_PROGRESS: OnboardingProgress = {
  generos: false,
  idiomas: false,
  regiones: false,
  redes: false,
  medios: false,
  preferencias: false,
};

type ContextValue = {
  loading: boolean;
  error: string | null;
  tipo: Tipo | null;
  progress: OnboardingProgress;
  steps: Step[];
  completedCount: number;
  totalCount: number;
  allDone: boolean;
  refresh: () => Promise<void>;
  /** href del siguiente paso, o "/onboarding/completado" si es el último. */
  nextHref: (current: StepKey) => string;
  /** href del paso anterior, o null si es el primero. */
  prevHref: (current: StepKey) => string | null;
};

const OnboardingContext = createContext<ContextValue | null>(null);

export function OnboardingProvider({ children }: { children: ReactNode }) {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tipo, setTipo] = useState<Tipo | null>(null);
  const [progress, setProgress] = useState<OnboardingProgress>(EMPTY_PROGRESS);

  const load = useCallback(async () => {
    try {
      const [me, prog] = await Promise.all([
        api.get<{ tipo: string }>("/auth/me"),
        api.get<OnboardingProgress>("/onboarding/progreso"),
      ]);
      setTipo(me.tipo === "curador" ? "curador" : "artista");
      setProgress({ ...EMPTY_PROGRESS, ...prog });
      setError(null);
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        router.replace("/login");
        return;
      }
      setError(
        err instanceof ApiError ? err.message : "No se pudo cargar tu progreso.",
      );
    } finally {
      setLoading(false);
    }
  }, [router]);

  useEffect(() => {
    void load();
  }, [load]);

  const order = tipo ? ORDER[tipo] : ORDER.artista;
  const steps: Step[] = order.map((key, i) => ({
    key,
    label: STEP_META[key].label,
    href: STEP_META[key].href,
    done: progress[key],
    index: i + 1,
  }));

  const completedCount = steps.filter((s) => s.done).length;
  const totalCount = steps.length;
  const allDone = totalCount > 0 && completedCount === totalCount;

  const nextHref = useCallback(
    (current: StepKey) => {
      const idx = order.indexOf(current);
      if (idx === -1 || idx === order.length - 1) {
        return "/onboarding/completado";
      }
      return STEP_META[order[idx + 1]].href;
    },
    [order],
  );

  const prevHref = useCallback(
    (current: StepKey) => {
      const idx = order.indexOf(current);
      if (idx <= 0) return null;
      return STEP_META[order[idx - 1]].href;
    },
    [order],
  );

  const value: ContextValue = {
    loading,
    error,
    tipo,
    progress,
    steps,
    completedCount,
    totalCount,
    allDone,
    refresh: load,
    nextHref,
    prevHref,
  };

  return createElement(OnboardingContext.Provider, { value }, children);
}

export function useOnboardingProgress(): ContextValue {
  const ctx = useContext(OnboardingContext);
  if (!ctx) {
    throw new Error(
      "useOnboardingProgress debe usarse dentro de <OnboardingProvider>",
    );
  }
  return ctx;
}
