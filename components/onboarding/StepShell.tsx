"use client";

import { useRouter } from "next/navigation";
import { ArrowLeft, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { useOnboardingProgress, type StepKey } from "@/hooks/useOnboardingProgress";

type StepShellProps = {
  currentKey: StepKey;
  title: string;
  description?: React.ReactNode;
  children: React.ReactNode;
  onContinue: () => void;
  continueLabel?: string;
  continueDisabled?: boolean;
  continueLoading?: boolean;
  /** Texto del enlace para saltar el paso (opcional). */
  skip?: { label: string; onClick: () => void } | null;
};

/** Contenedor común de un paso del wizard: encabezado, contenido y navegación. */
export function StepShell({
  currentKey,
  title,
  description,
  children,
  onContinue,
  continueLabel = "Continuar",
  continueDisabled = false,
  continueLoading = false,
  skip = null,
}: StepShellProps) {
  const router = useRouter();
  const { prevHref, steps } = useOnboardingProgress();
  const prev = prevHref(currentKey);
  const isLast = steps.length > 0 && steps[steps.length - 1].key === currentKey;

  return (
    <div className="animate-onboarding-in flex flex-col">
      <header className="mb-6">
        <h1 className="text-2xl font-bold tracking-tight text-text sm:text-3xl">
          {title}
        </h1>
        {description && (
          <p className="mt-2 max-w-xl text-sm leading-relaxed text-text-muted">
            {description}
          </p>
        )}
      </header>

      <div className="flex-1">{children}</div>

      <footer className="mt-8 flex items-center justify-between gap-3 border-t border-border pt-5">
        <div>
          {prev && (
            <Button variant="ghost" onClick={() => router.push(prev)}>
              <ArrowLeft size={16} />
              Atrás
            </Button>
          )}
        </div>
        <div className="flex items-center gap-3">
          {skip && (
            <button
              type="button"
              onClick={skip.onClick}
              className="text-sm text-text-muted transition-colors hover:text-primary-light"
            >
              {skip.label}
            </button>
          )}
          <Button
            onClick={onContinue}
            disabled={continueDisabled}
            loading={continueLoading}
          >
            {isLast ? "Finalizar" : continueLabel}
            {!isLast && <ArrowRight size={16} />}
          </Button>
        </div>
      </footer>
    </div>
  );
}
