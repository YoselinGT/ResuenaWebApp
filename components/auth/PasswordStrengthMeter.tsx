"use client";

import { Check, X } from "lucide-react";
import { passwordChecks, passwordScore } from "@/lib/password";
import { cn } from "@/lib/utils";

type Props = {
  password: string;
  /** Muestra la lista detallada de requisitos. */
  showChecklist?: boolean;
};

const LABELS = ["Muy débil", "Débil", "Aceptable", "Fuerte", "Excelente"];
const BAR_COLORS = [
  "bg-danger",
  "bg-danger",
  "bg-warning",
  "bg-primary-light",
  "bg-success",
];

export function PasswordStrengthMeter({ password, showChecklist = true }: Props) {
  const score = passwordScore(password);
  const checks = passwordChecks(password);
  const show = password.length > 0;

  return (
    <div className="flex flex-col gap-2" aria-live="polite">
      <div className="flex items-center gap-1.5">
        {[0, 1, 2, 3].map((i) => (
          <span
            key={i}
            className={cn(
              "h-1.5 flex-1 rounded-full transition-colors duration-200",
              show && i < score ? BAR_COLORS[score] : "bg-border",
            )}
          />
        ))}
      </div>
      {show && (
        <p className="text-xs font-medium text-text-muted">
          Seguridad:{" "}
          <span
            className={cn(
              score <= 1 && "text-danger",
              score === 2 && "text-warning",
              score === 3 && "text-primary-light",
              score >= 4 && "text-success",
            )}
          >
            {LABELS[score]}
          </span>
        </p>
      )}
      {showChecklist && show && (
        <ul className="mt-0.5 grid grid-cols-1 gap-1 sm:grid-cols-2">
          {checks.map((c) => (
            <li
              key={c.label}
              className={cn(
                "flex items-center gap-1.5 text-xs",
                c.ok ? "text-success" : "text-text-muted",
              )}
            >
              {c.ok ? (
                <Check size={13} className="shrink-0" />
              ) : (
                <X size={13} className="shrink-0 opacity-60" />
              )}
              {c.label}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
