"use client";

import { usePathname } from "next/navigation";
import { Loader2 } from "lucide-react";
import { Logo } from "@/components/ui/Logo";
import { Alert } from "@/components/ui/Alert";
import { StepperNav } from "@/components/onboarding/StepperNav";
import {
  OnboardingProvider,
  useOnboardingProgress,
  type StepKey,
} from "@/hooks/useOnboardingProgress";

const STEP_KEYS: StepKey[] = ["generos", "idiomas", "regiones", "medios", "redes"];

function keyFromPath(pathname: string): StepKey | null {
  const seg = pathname.split("/").filter(Boolean).pop() ?? "";
  return (STEP_KEYS as string[]).includes(seg) ? (seg as StepKey) : null;
}

function WizardChrome({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { loading, error, steps, completedCount, totalCount } =
    useOnboardingProgress();
  const currentKey = keyFromPath(pathname);

  // Pantalla de éxito (u otras sin paso): sin stepper, contenido a pantalla completa.
  if (!currentKey) {
    return <div className="mx-auto w-full max-w-2xl px-4 py-10">{children}</div>;
  }

  if (loading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <Loader2 className="animate-spin text-primary-light" size={36} />
      </div>
    );
  }

  const pct = totalCount > 0 ? Math.round((completedCount / totalCount) * 100) : 0;

  return (
    <div className="mx-auto w-full max-w-5xl px-4 py-8 sm:px-6">
      <header className="mb-8 flex flex-col gap-5">
        <div className="flex items-center justify-between">
          <Logo width={150} priority />
          <span className="text-sm text-text-muted">
            Paso {Math.min(completedCount + 1, totalCount)} de {totalCount}
          </span>
        </div>
        <div
          className="onboarding-progress-bar"
          style={{ ["--progress-width" as string]: `${pct}%` }}
          role="progressbar"
          aria-valuenow={pct}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label="Progreso del onboarding"
        />
      </header>

      {error && (
        <Alert variant="error" className="mb-6">
          {error}
        </Alert>
      )}

      <div className="grid grid-cols-1 gap-8 md:grid-cols-[220px_1fr]">
        <aside className="md:sticky md:top-8 md:self-start">
          <StepperNav steps={steps} currentKey={currentKey} />
        </aside>
        <main className="min-w-0 rounded-lg border border-border bg-surface p-6 shadow-glow sm:p-8">
          {children}
        </main>
      </div>
    </div>
  );
}

export default function OnboardingLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="onboarding-shell min-h-screen">
      <OnboardingProvider>
        <WizardChrome>{children}</WizardChrome>
      </OnboardingProvider>
    </div>
  );
}
