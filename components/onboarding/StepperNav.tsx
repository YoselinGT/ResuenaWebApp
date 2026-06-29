"use client";

import Link from "next/link";
import { Check } from "lucide-react";
import { cn } from "@/lib/utils";
import type { Step, StepKey } from "@/hooks/useOnboardingProgress";

type StepperNavProps = {
  steps: Step[];
  currentKey: StepKey;
};

/**
 * Navegación del wizard: vertical en desktop (lateral), horizontal en móvil.
 * Cada paso muestra su estado (completado / activo / pendiente) y enlaza a su ruta.
 */
export function StepperNav({ steps, currentKey }: StepperNavProps) {
  return (
    <nav aria-label="Pasos de onboarding">
      {/* Desktop: lista vertical */}
      <ol className="hidden gap-1 md:flex md:flex-col">
        {steps.map((step) => {
          const active = step.key === currentKey;
          return (
            <li key={step.key}>
              <Link
                href={step.href}
                aria-current={active ? "step" : undefined}
                className={cn(
                  "group flex items-center gap-3 rounded-md px-3 py-2.5 transition-colors",
                  active ? "bg-surface-2" : "hover:bg-surface-2/60",
                )}
              >
                <StepBadge step={step} active={active} />
                <span
                  className={cn(
                    "text-sm font-medium transition-colors",
                    active
                      ? "text-text"
                      : step.done
                        ? "text-text-muted"
                        : "text-text-muted/80",
                  )}
                >
                  {step.label}
                </span>
              </Link>
            </li>
          );
        })}
      </ol>

      {/* Móvil: fila horizontal compacta */}
      <ol className="flex items-center justify-between gap-1 md:hidden">
        {steps.map((step, i) => {
          const active = step.key === currentKey;
          return (
            <li key={step.key} className="flex flex-1 items-center">
              <Link
                href={step.href}
                aria-current={active ? "step" : undefined}
                aria-label={step.label}
                className="flex flex-col items-center gap-1"
              >
                <StepBadge step={step} active={active} />
              </Link>
              {i < steps.length - 1 && (
                <span
                  className={cn(
                    "mx-1 h-px flex-1",
                    step.done ? "bg-primary/50" : "bg-border",
                  )}
                  aria-hidden
                />
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}

function StepBadge({ step, active }: { step: Step; active: boolean }) {
  return (
    <span
      className={cn(
        "flex h-7 w-7 shrink-0 items-center justify-center rounded-full border text-xs font-semibold transition-all",
        step.done
          ? "border-primary bg-primary text-text"
          : active
            ? "border-primary text-primary-light shadow-glow"
            : "border-border text-text-muted",
      )}
    >
      {step.done ? <Check size={14} /> : step.index}
    </span>
  );
}
