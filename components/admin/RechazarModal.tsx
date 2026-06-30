"use client";

import { useEffect, useState } from "react";
import { X } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/Button";
import { Alert } from "@/components/ui/Alert";

type Props = {
  solicitudId: string;
  nombre: string;
  onClose: () => void;
  onRejected: () => void;
};

export function RechazarModal({ solicitudId, nombre, onClose, onRejected }: Props) {
  const [motivo, setMotivo] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [onClose]);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (motivo.trim().length < 3) {
      setError("Indica un motivo (mínimo 3 caracteres).");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      await api.post(`/admin/solicitudes/${solicitudId}/rechazar`, {
        motivo: motivo.trim(),
      });
      onRejected();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo rechazar.");
      setLoading(false);
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="rechazar-title"
    >
      <div className="absolute inset-0 bg-base/80 backdrop-blur-sm" onClick={onClose} aria-hidden />
      <div className="auth-enter relative w-full max-w-md rounded-lg border border-border bg-surface p-6 shadow-glow-lg">
        <button
          type="button"
          onClick={onClose}
          aria-label="Cerrar"
          className="absolute right-4 top-4 text-text-muted transition-colors hover:text-text"
        >
          <X size={20} />
        </button>
        <h2 id="rechazar-title" className="text-lg font-bold text-text">
          Rechazar solicitud
        </h2>
        <p className="mt-1 text-sm text-text-muted">
          Se enviará el motivo a <span className="text-text">{nombre}</span> por correo.
        </p>
        <form onSubmit={submit} className="mt-4 flex flex-col gap-4">
          {error && <Alert variant="error">{error}</Alert>}
          <textarea
            value={motivo}
            onChange={(e) => setMotivo(e.target.value)}
            rows={4}
            required
            placeholder="Motivo del rechazo…"
            className={cn(
              "w-full resize-none rounded-md bg-surface-2 px-4 py-2.5 text-sm text-text",
              "border border-border placeholder:text-text-muted/60",
              "focus:outline-none focus:border-primary focus:ring-2 focus:ring-[var(--accent-glow)]",
            )}
          />
          <div className="flex justify-end gap-2">
            <Button type="button" variant="ghost" onClick={onClose}>
              Cancelar
            </Button>
            <Button type="submit" variant="danger" loading={loading}>
              Rechazar
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
