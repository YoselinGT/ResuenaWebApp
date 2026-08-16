"use client";

import { useState, useCallback } from "react";
import {
  ChevronDown,
  ChevronRight,
  Pencil,
  Plus,
  Trash2,
  Check,
  X,
} from "lucide-react";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/Button";
import type { Categoria, GeneroAdmin } from "@/app/(dashboard)/admin/generos/page";

type Props = {
  generos: GeneroAdmin[];
  onRefresh: () => void;
};

export function GenerosTable({ generos, onRefresh }: Props) {
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [editingGenero, setEditingGenero] = useState<number | null>(null);
  const [editNombre, setEditNombre] = useState("");
  const [addingCategoria, setAddingCategoria] = useState<number | null>(null);
  const [newCategoriaNombre, setNewCategoriaNombre] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const toggleExpand = (id: number) => {
    setExpandedId(expandedId === id ? null : id);
    setEditingGenero(null);
    setAddingCategoria(null);
  };

  const startEditGenero = (g: GeneroAdmin) => {
    setEditingGenero(g.id);
    setEditNombre(g.nombre);
    setError(null);
  };

  const saveGenero = useCallback(
    async (id: number) => {
      if (!editNombre.trim()) return;
      setSaving(true);
      setError(null);
      try {
        await api.patch(`/admin/generos/${id}`, { nombre: editNombre.trim() });
        setEditingGenero(null);
        onRefresh();
      } catch {
        setError("No se pudo guardar el género.");
      } finally {
        setSaving(false);
      }
    },
    [editNombre, onRefresh],
  );

  const toggleGeneroActivo = useCallback(
    async (g: GeneroAdmin) => {
      try {
        await api.patch(`/admin/generos/${g.id}`, { activo: !g.activo });
        onRefresh();
      } catch {
        setError("No se pudo cambiar el estado del género.");
      }
    },
    [onRefresh],
  );

  const deleteGenero = useCallback(
    async (id: number) => {
      if (!confirm("¿Eliminar este género?")) return;
      try {
        await api.del(`/admin/generos/${id}`);
        onRefresh();
      } catch (err: unknown) {
        const msg =
          err && typeof err === "object" && "message" in err
            ? String(err.message)
            : "No se pudo eliminar el género.";
        setError(msg);
      }
    },
    [onRefresh],
  );

  const addCategoria = useCallback(
    async (generoId: number) => {
      if (!newCategoriaNombre.trim()) return;
      setSaving(true);
      setError(null);
      try {
        await api.post(`/admin/generos/${generoId}/categorias`, {
          nombre: newCategoriaNombre.trim(),
        });
        setAddingCategoria(null);
        setNewCategoriaNombre("");
        onRefresh();
      } catch {
        setError("No se pudo crear la categoría.");
      } finally {
        setSaving(false);
      }
    },
    [newCategoriaNombre, onRefresh],
  );

  const toggleCategoriaActivo = useCallback(
    async (cat: Categoria) => {
      try {
        await api.patch(`/admin/generos/categorias/${cat.id}`, {
          activo: !cat.activo,
        });
        onRefresh();
      } catch {
        setError("No se pudo cambiar el estado de la categoría.");
      }
    },
    [onRefresh],
  );

  const deleteCategoria = useCallback(
    async (id: number) => {
      if (!confirm("¿Eliminar esta categoría?")) return;
      try {
        await api.del(`/admin/generos/categorias/${id}`);
        onRefresh();
      } catch (err: unknown) {
        const msg =
          err && typeof err === "object" && "message" in err
            ? String(err.message)
            : "No se pudo eliminar la categoría.";
        setError(msg);
      }
    },
    [onRefresh],
  );

  return (
    <div className="rounded-xl border border-border bg-surface overflow-hidden">
      {error && (
        <div className="px-5 py-2 bg-danger/10 text-danger text-xs border-b border-border">
          {error}
        </div>
      )}

      <div className="divide-y divide-border">
        {generos.length === 0 && (
          <div className="px-5 py-10 text-center text-text-muted text-sm">
            No hay géneros creados.
          </div>
        )}

        {generos.map((g) => (
          <div key={g.id}>
            {/* Fila del género */}
            <div className="flex items-center gap-3 px-5 py-3 hover:bg-surface-2/50 transition-colors">
              <button
                onClick={() => toggleExpand(g.id)}
                className="p-1 text-text-muted hover:text-text transition-colors"
              >
                {expandedId === g.id ? (
                  <ChevronDown size={16} />
                ) : (
                  <ChevronRight size={16} />
                )}
              </button>

              {editingGenero === g.id ? (
                <div className="flex flex-1 items-center gap-2">
                  <input
                    type="text"
                    value={editNombre}
                    onChange={(e) => setEditNombre(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && saveGenero(g.id)}
                    autoFocus
                    className="flex-1 rounded border border-border bg-surface px-2 py-1 text-sm text-text focus:outline-none focus:ring-1 focus:ring-primary"
                  />
                  <button
                    onClick={() => saveGenero(g.id)}
                    disabled={saving || !editNombre.trim()}
                    className="p-1.5 text-success hover:bg-success/10 rounded transition-colors disabled:opacity-30"
                  >
                    <Check size={14} />
                  </button>
                  <button
                    onClick={() => setEditingGenero(null)}
                    className="p-1.5 text-text-muted hover:bg-surface-2 rounded transition-colors"
                  >
                    <X size={14} />
                  </button>
                </div>
              ) : (
                <>
                  <span className="flex-1 font-medium text-text">
                    {g.nombre}
                  </span>
                  <span className="text-xs text-text-muted">
                    {g.categorias.length} categoría
                    {g.categorias.length !== 1 ? "s" : ""}
                  </span>
                  <span
                    className={cn(
                      "rounded-full px-2 py-0.5 text-[10px] font-semibold cursor-pointer",
                      g.activo
                        ? "bg-success/15 text-success"
                        : "bg-text-muted/15 text-text-muted",
                    )}
                    onClick={() => toggleGeneroActivo(g)}
                    title={g.activo ? "Desactivar" : "Activar"}
                  >
                    {g.activo ? "Activo" : "Inactivo"}
                  </span>
                  <button
                    onClick={() => startEditGenero(g)}
                    className="p-1.5 text-text-muted hover:text-text hover:bg-surface-2 rounded transition-colors"
                    title="Editar"
                  >
                    <Pencil size={14} />
                  </button>
                  <button
                    onClick={() => deleteGenero(g.id)}
                    className="p-1.5 text-text-muted hover:text-danger hover:bg-danger/10 rounded transition-colors"
                    title="Eliminar"
                  >
                    <Trash2 size={14} />
                  </button>
                </>
              )}
            </div>

            {/* Categorías (acordeón) */}
            {expandedId === g.id && (
              <div className="bg-surface-2/30 border-t border-border/50">
                {g.categorias.map((cat) => (
                  <div
                    key={cat.id}
                    className="flex items-center gap-3 pl-12 pr-5 py-2 hover:bg-surface-2/50 transition-colors"
                  >
                    <span className="flex-1 text-sm text-text">
                      {cat.nombre}
                    </span>
                    <span
                      className={cn(
                        "rounded-full px-2 py-0.5 text-[10px] font-semibold cursor-pointer",
                        cat.activo
                          ? "bg-success/15 text-success"
                          : "bg-text-muted/15 text-text-muted",
                      )}
                      onClick={() => toggleCategoriaActivo(cat)}
                      title={cat.activo ? "Desactivar" : "Activar"}
                    >
                      {cat.activo ? "Activo" : "Inactivo"}
                    </span>
                    <button
                      onClick={() => deleteCategoria(cat.id)}
                      className="p-1 text-text-muted hover:text-danger hover:bg-danger/10 rounded transition-colors"
                      title="Eliminar"
                    >
                      <Trash2 size={12} />
                    </button>
                  </div>
                ))}

                {/* Agregar categoría */}
                {addingCategoria === g.id ? (
                  <div className="flex items-center gap-2 pl-12 pr-5 py-2">
                    <input
                      type="text"
                      value={newCategoriaNombre}
                      onChange={(e) => setNewCategoriaNombre(e.target.value)}
                      onKeyDown={(e) =>
                        e.key === "Enter" && addCategoria(g.id)
                      }
                      placeholder="Nombre de la categoría"
                      autoFocus
                      className="flex-1 rounded border border-border bg-surface px-2 py-1 text-sm text-text focus:outline-none focus:ring-1 focus:ring-primary"
                    />
                    <button
                      onClick={() => addCategoria(g.id)}
                      disabled={saving || !newCategoriaNombre.trim()}
                      className="p-1.5 text-success hover:bg-success/10 rounded transition-colors disabled:opacity-30"
                    >
                      <Check size={14} />
                    </button>
                    <button
                      onClick={() => {
                        setAddingCategoria(null);
                        setNewCategoriaNombre("");
                      }}
                      className="p-1.5 text-text-muted hover:bg-surface-2 rounded transition-colors"
                    >
                      <X size={14} />
                    </button>
                  </div>
                ) : (
                  <div className="pl-12 pr-5 py-2">
                    <button
                      onClick={() => setAddingCategoria(g.id)}
                      className="flex items-center gap-1.5 text-xs text-text-muted hover:text-primary-light transition-colors"
                    >
                      <Plus size={12} /> Agregar categoría
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
