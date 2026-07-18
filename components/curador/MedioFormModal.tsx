"use client";

import { useEffect, useState } from "react";
import { X } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import { Alert } from "@/components/ui/Alert";
import {
  MedioForm,
  type Genero,
  type MedioFormValues,
} from "@/components/onboarding/MedioForm";
import type { Medio } from "@/components/curador/MedioCard";

type Props = {
  generos: Genero[];
  initial?: Medio | null;
  onClose: () => void;
  onSaved: (medio: Medio) => void;
};

export function MedioFormModal({ generos, initial, onClose, onSaved }: Props) {
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const editando = Boolean(initial);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [onClose]);

  async function submit(values: MedioFormValues) {
    setSubmitting(true);
    setError(null);
    const payload = {
      nombre: values.nombre,
      tipo: values.tipo,
      url: values.url,
      descripcion: values.descripcion,
      audiencia_estimada: values.audiencia_estimada,
      precio_creditos: values.precio_creditos,
      descripcion_precio: values.descripcion_precio,
      generos_especializados: values.genero_ids,
    };
    try {
      const medio = initial
        ? await api.patch<Medio>(`/curador/medios/${initial.id}`, payload)
        : await api.post<Medio>("/curador/medios", payload);
      onSaved(medio);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "No se pudo guardar el medio.",
      );
      setSubmitting(false);
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center overflow-y-auto p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="medio-modal-title"
    >
      <div className="absolute inset-0 bg-base/80 backdrop-blur-sm" onClick={onClose} aria-hidden />
      <div className="auth-enter relative my-8 w-full max-w-lg rounded-lg border border-border bg-surface p-6 shadow-glow-lg">
        <div className="mb-4 flex items-center justify-between">
          <h2 id="medio-modal-title" className="text-lg font-bold text-text">
            {editando ? "Editar canal" : "Añadir canal"}
          </h2>
          <button
            type="button"
            onClick={onClose}
            aria-label="Cerrar"
            className="text-text-muted transition-colors hover:text-text"
          >
            <X size={20} />
          </button>
        </div>

        {error && (
          <div className="mb-4">
            <Alert variant="error">{error}</Alert>
          </div>
        )}

        <MedioForm
          generos={generos}
          initial={initial ?? undefined}
          submitting={submitting}
          submitLabel={editando ? "Guardar cambios" : "Añadir canal"}
          onSubmit={submit}
          onCancel={onClose}
        />
      </div>
    </div>
  );
}
