"use client";

import { Star, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { cn } from "@/lib/utils";
import { RED_PLATFORMS, platformMeta } from "./RedSocialRow";

export type RedEditable = {
  tipo: string;
  url: string;
  es_principal: boolean;
};

type Props = {
  red: RedEditable;
  index: number;
  total: number;
  onChange: (updated: RedEditable) => void;
  onRemove: () => void;
  onSetPrincipal: () => void;
};

export function RedSocialEditableRow({
  red,
  index,
  total,
  onChange,
  onRemove,
  onSetPrincipal,
}: Props) {
  const meta = platformMeta(red.tipo);
  const Icon = meta.Icon;

  return (
    <div className="flex flex-col gap-2 rounded-md border border-border bg-surface-2/50 p-3 sm:flex-row sm:items-center sm:gap-3">
      {/* Tipo */}
      <div className="flex items-center gap-2 sm:w-40">
        <select
          value={red.tipo}
          onChange={(e) => onChange({ ...red, tipo: e.target.value })}
          className={cn(
            "h-9 w-full rounded-md border border-border bg-surface-2 px-2 text-sm text-text",
            "focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary",
            !red.tipo && "text-text-muted",
          )}
        >
          <option value="" disabled>
            Tipo…
          </option>
          {RED_PLATFORMS.map((p) => (
            <option key={p.value} value={p.value}>
              {p.label}
            </option>
          ))}
        </select>
      </div>

      {/* URL */}
      <div className="flex flex-1 items-center gap-2">
        {red.tipo && (
          <span className="hidden shrink-0 text-text-muted sm:block">
            <Icon size={16} />
          </span>
        )}
        <input
          type="url"
          value={red.url}
          onChange={(e) => onChange({ ...red, url: e.target.value })}
          placeholder={meta.placeholder}
          className="h-9 w-full rounded-md border border-border bg-surface-2 px-3 text-sm text-text placeholder:text-text-muted/50 focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary"
        />
      </div>

      {/* Principal + Remove */}
      <div className="flex items-center gap-1 sm:shrink-0">
        <button
          type="button"
          onClick={onSetPrincipal}
          title={red.es_principal ? "Red principal" : "Marcar como principal"}
          className={cn(
            "flex h-9 w-9 items-center justify-center rounded-md transition-colors",
            red.es_principal
              ? "text-warning"
              : "text-text-muted/40 hover:text-text-muted",
          )}
        >
          <Star
            size={18}
            fill={red.es_principal ? "currentColor" : "none"}
          />
        </button>
        {total > 1 && (
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={onRemove}
            aria-label="Eliminar red"
          >
            <Trash2 size={16} />
          </Button>
        )}
      </div>
    </div>
  );
}
