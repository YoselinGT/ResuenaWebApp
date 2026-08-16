"use client";

import { useState, useEffect } from "react";
import { ChevronDown, ChevronRight, Check } from "lucide-react";
import { cn } from "@/lib/utils";

type Categoria = {
  id: number;
  nombre: string;
  activo: boolean;
};

type Genero = {
  id: number;
  nombre: string;
  categorias: Categoria[];
};

type Props = {
  generos: Genero[];
  selectedIds: number[];
  onChange: (ids: number[]) => void;
  className?: string;
};

export function GenerosCategoriasPicker({
  generos,
  selectedIds,
  onChange,
  className,
}: Props) {
  const [expandedIds, setExpandedIds] = useState<Set<number>>(new Set());

  // Expandir géneros que tienen categorías seleccionadas
  useEffect(() => {
    const toExpand = new Set<number>();
    for (const g of generos) {
      if (g.categorias.some((c) => selectedIds.includes(c.id))) {
        toExpand.add(g.id);
      }
    }
    if (toExpand.size > 0) {
      setExpandedIds((prev) => new Set([...prev, ...toExpand]));
    }
  }, [generos, selectedIds]);

  const toggleExpand = (id: number) => {
    setExpandedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const toggleCategoria = (catId: number) => {
    if (selectedIds.includes(catId)) {
      onChange(selectedIds.filter((id) => id !== catId));
    } else {
      onChange([...selectedIds, catId]);
    }
  };

  const selectedCount = selectedIds.length;

  return (
    <div className={cn("rounded-lg border border-border bg-surface", className)}>
      {selectedCount > 0 && (
        <div className="px-3 py-2 border-b border-border text-xs text-text-muted">
          {selectedCount} categoría{selectedCount !== 1 ? "s" : ""} seleccionada
          {selectedCount !== 1 ? "s" : ""}
        </div>
      )}

      <div className="divide-y divide-border/50 max-h-[400px] overflow-y-auto">
        {generos.map((genero) => {
          const isExpanded = expandedIds.has(genero.id);
          const selectedInGenre = genero.categorias.filter((c) =>
            selectedIds.includes(c.id),
          );

          return (
            <div key={genero.id}>
              {/* Fila del género */}
              <button
                type="button"
                onClick={() => toggleExpand(genero.id)}
                className="flex w-full items-center gap-2 px-3 py-2.5 hover:bg-surface-2/50 transition-colors text-left"
              >
                {isExpanded ? (
                  <ChevronDown size={14} className="text-text-muted shrink-0" />
                ) : (
                  <ChevronRight
                    size={14}
                    className="text-text-muted shrink-0"
                  />
                )}
                <span className="flex-1 text-sm font-medium text-text">
                  {genero.nombre}
                </span>
                {selectedInGenre.length > 0 && (
                  <span className="rounded-full bg-primary/15 px-2 py-0.5 text-[10px] font-semibold text-primary-light">
                    {selectedInGenre.length}
                  </span>
                )}
              </button>

              {/* Categorías */}
              {isExpanded && (
                <div className="bg-surface-2/30">
                  {genero.categorias.length === 0 ? (
                    <p className="pl-9 pr-3 py-2 text-xs text-text-muted">
                      Sin categorías
                    </p>
                  ) : (
                    genero.categorias.map((cat) => {
                      const isSelected = selectedIds.includes(cat.id);
                      return (
                        <button
                          key={cat.id}
                          type="button"
                          onClick={() => toggleCategoria(cat.id)}
                          className={cn(
                            "flex w-full items-center gap-2 pl-9 pr-3 py-2 transition-colors text-left",
                            isSelected
                              ? "bg-primary/10"
                              : "hover:bg-surface-2/50",
                          )}
                        >
                          <div
                            className={cn(
                              "w-4 h-4 rounded border flex items-center justify-center shrink-0 transition-colors",
                              isSelected
                                ? "bg-primary border-primary text-white"
                                : "border-border",
                            )}
                          >
                            {isSelected && <Check size={10} />}
                          </div>
                          <span
                            className={cn(
                              "text-sm",
                              isSelected
                                ? "text-text font-medium"
                                : "text-text-muted",
                            )}
                          >
                            {cat.nombre}
                          </span>
                        </button>
                      );
                    })
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
