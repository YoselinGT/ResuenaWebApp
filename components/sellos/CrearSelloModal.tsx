"use client";

import { useEffect, useRef, useState } from "react";
import { Building2, Link2, X } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Alert } from "@/components/ui/Alert";

export type Sello = {
  id: string;
  nombre: string;
  descripcion: string | null;
  website: string | null;
  logo_url: string | null;
  rol: string | null;
};

type Props = {
  onClose: () => void;
  onCreated: (sello: Sello) => void;
};

export function CrearSelloModal({ onClose, onCreated }: Props) {
  const [nombre, setNombre] = useState("");
  const [descripcion, setDescripcion] = useState("");
  const [website, setWebsite] = useState("");
  const [logo, setLogo] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [onClose]);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (nombre.trim().length < 2) {
      setError("El nombre del sello debe tener al menos 2 caracteres.");
      return;
    }
    if (logo && logo.type !== "image/jpeg") {
      setError("El logo debe ser una imagen JPEG.");
      return;
    }
    setError(null);
    setLoading(true);
    try {
      const form = new FormData();
      form.append("nombre", nombre.trim());
      if (descripcion.trim()) form.append("descripcion", descripcion.trim());
      if (website.trim()) form.append("website", website.trim());
      if (logo) form.append("logo", logo);
      const sello = await api.upload<Sello>("/sellos", form);
      onCreated(sello);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "No se pudo crear el sello. Reintenta.",
      );
      setLoading(false);
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="crear-sello-title"
    >
      <div
        className="absolute inset-0 bg-base/80 backdrop-blur-sm"
        onClick={onClose}
        aria-hidden
      />
      <div className="auth-enter relative w-full max-w-md rounded-lg border border-border bg-surface p-7 shadow-glow-lg">
        <button
          type="button"
          onClick={onClose}
          aria-label="Cerrar"
          className="absolute right-4 top-4 text-text-muted transition-colors hover:text-text"
        >
          <X size={20} />
        </button>

        <div className="mb-5 flex items-center gap-2 text-primary-light">
          <Building2 size={20} />
          <h2 id="crear-sello-title" className="text-lg font-bold text-text">
            Crear mi sello
          </h2>
        </div>

        <form onSubmit={submit} className="flex flex-col gap-4" noValidate>
          {error && <Alert variant="error">{error}</Alert>}

          <Input
            label="Nombre del sello"
            required
            value={nombre}
            onChange={(e) => setNombre(e.target.value)}
            placeholder="Ej. Luna Records"
          />

          <div className="flex flex-col gap-1.5">
            <label htmlFor="sello-desc" className="text-sm font-medium text-text-muted">
              Descripción (opcional)
            </label>
            <textarea
              id="sello-desc"
              value={descripcion}
              onChange={(e) => setDescripcion(e.target.value)}
              rows={3}
              className={cn(
                "w-full rounded-md bg-surface-2 px-4 py-2.5 text-sm text-text",
                "border border-border placeholder:text-text-muted/60 resize-none",
                "focus:outline-none focus:border-primary focus:ring-2 focus:ring-[var(--accent-glow)]",
              )}
              placeholder="¿Qué representa tu sello?"
            />
          </div>

          <Input
            label="Sitio web (opcional)"
            type="url"
            value={website}
            onChange={(e) => setWebsite(e.target.value)}
            leftIcon={<Link2 size={16} />}
            placeholder="https://tu-sello.com"
          />

          <div className="flex flex-col gap-1.5">
            <span className="text-sm font-medium text-text-muted">Logo (opcional, JPEG)</span>
            <div className="flex items-center gap-3">
              <Button
                type="button"
                variant="secondary"
                size="sm"
                onClick={() => fileRef.current?.click()}
              >
                Elegir imagen
              </Button>
              <span className="truncate text-xs text-text-muted">
                {logo ? logo.name : "Ningún archivo"}
              </span>
              <input
                ref={fileRef}
                type="file"
                accept="image/jpeg"
                className="hidden"
                onChange={(e) => setLogo(e.target.files?.[0] ?? null)}
              />
            </div>
          </div>

          <Button type="submit" loading={loading} fullWidth className="mt-1">
            Crear sello
          </Button>
        </form>
      </div>
    </div>
  );
}
