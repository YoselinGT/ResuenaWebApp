"use client";

import { Check } from "lucide-react";
import { cn } from "@/lib/utils";

type GenreChipProps = {
  label: string;
  selected: boolean;
  onToggle: () => void;
  size?: "sm" | "md";
};

/** Chip seleccionable (pill) para selección múltiple de géneros u opciones. */
export function GenreChip({
  label,
  selected,
  onToggle,
  size = "md",
}: GenreChipProps) {
  return (
    <button
      type="button"
      role="checkbox"
      aria-checked={selected}
      onClick={onToggle}
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border font-medium transition-all duration-150 active:scale-[0.97]",
        size === "md" ? "px-4 py-2 text-sm" : "px-3 py-1.5 text-xs",
        selected
          ? "border-primary bg-primary/15 text-text shadow-glow"
          : "border-border bg-surface-2 text-text-muted hover:border-primary/40 hover:text-text",
      )}
    >
      {selected && <Check size={size === "md" ? 15 : 13} className="shrink-0" />}
      {label}
    </button>
  );
}
