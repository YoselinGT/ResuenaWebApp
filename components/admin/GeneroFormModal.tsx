"use client";

import { useState } from "react";
import { X } from "lucide-react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/Button";

type Props = {
  onClose: () => void;
  onSaved: () => void;
};

export function GeneroFormModal({ onClose, onSaved }: Props) {
  const [nombre, setNombre] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!nombre.trim()) return;

    setSaving(true);
    setError(null);
    try {
      await api.post("/admin/generos", { nombre: nombre.trim() });
      onSaved();
    } catch {
      setError("No se pudo crear el género.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={onClose}
      />
      <div className="relative w-full max-w-md rounded-xl border border-border bg-surface p-6 shadow-xl">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-text">Nuevo género</h2>
          <button
            onClick={onClose}
            className="p-1.5 text-text-muted hover:text-text rounded-lg hover:bg-surface-2 transition-colors"
          >
            <X size={18} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div>
            <label
              htmlFor="genero-nombre"
              className="block text-sm font-medium text-text-muted mb-1.5"
            >
              Nombre del género
            </label>
            <input
              id="genero-nombre"
              type="text"
              value={nombre}
              onChange={(e) => setNombre(e.target.value)}
              placeholder="Ej: Urbano, Rock, Pop..."
              autoFocus
              className="w-full rounded-lg border border-border bg-surface-2 px-3 py-2 text-sm text-text placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>

          {error && (
            <p className="text-sm text-danger">{error}</p>
          )}

          <div className="flex justify-end gap-2">
            <Button
              type="button"
              variant="ghost"
              onClick={onClose}
              disabled={saving}
            >
              Cancelar
            </Button>
            <Button
              type="submit"
              disabled={saving || !nombre.trim()}
              loading={saving}
            >
              Crear género
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
