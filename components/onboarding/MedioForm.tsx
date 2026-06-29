"use client";

import { useState } from "react";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { GenreChip } from "@/components/onboarding/GenreChip";
import { cn } from "@/lib/utils";

/** Tipos de medio de curador (espeja el ENUM TipoMedio). */
export const MEDIO_TYPES: Array<{ value: string; label: string }> = [
  { value: "playlist", label: "Playlist" },
  { value: "blog", label: "Blog" },
  { value: "instagram", label: "Instagram" },
  { value: "tiktok", label: "TikTok" },
  { value: "youtube", label: "YouTube" },
  { value: "facebook", label: "Facebook" },
  { value: "twitter", label: "X / Twitter" },
  { value: "radio", label: "Radio / Podcast" },
  { value: "website", label: "Sitio web" },
  { value: "eventos", label: "Eventos" },
  { value: "otro", label: "Otro" },
];

export type Genero = { id: number; nombre: string };

export type MedioFormValues = {
  nombre: string;
  tipo: string;
  url: string | null;
  descripcion: string | null;
  audiencia_estimada: number | null;
  genero_ids: number[];
};

type MedioFormProps = {
  generos: Genero[];
  initial?: Partial<MedioFormValues>;
  submitting?: boolean;
  submitLabel?: string;
  onSubmit: (values: MedioFormValues) => void;
  onCancel?: () => void;
};

export function MedioForm({
  generos,
  initial,
  submitting,
  submitLabel = "Agregar canal",
  onSubmit,
  onCancel,
}: MedioFormProps) {
  const [nombre, setNombre] = useState(initial?.nombre ?? "");
  const [tipo, setTipo] = useState(initial?.tipo ?? "");
  const [url, setUrl] = useState(initial?.url ?? "");
  const [descripcion, setDescripcion] = useState(initial?.descripcion ?? "");
  const [audiencia, setAudiencia] = useState(
    initial?.audiencia_estimada != null ? String(initial.audiencia_estimada) : "",
  );
  const [generoIds, setGeneroIds] = useState<number[]>(initial?.genero_ids ?? []);
  const [error, setError] = useState<string | null>(null);

  function toggleGenero(id: number) {
    setGeneroIds((prev) =>
      prev.includes(id) ? prev.filter((g) => g !== id) : [...prev, id],
    );
  }

  function submit(e: React.FormEvent) {
    e.preventDefault();
    if (nombre.trim().length < 1) {
      setError("Ponle un nombre a tu canal.");
      return;
    }
    if (!tipo) {
      setError("Elige el tipo de canal.");
      return;
    }
    setError(null);
    onSubmit({
      nombre: nombre.trim(),
      tipo,
      url: url.trim() || null,
      descripcion: descripcion.trim() || null,
      audiencia_estimada: audiencia ? Number(audiencia) : null,
      genero_ids: generoIds,
    });
  }

  return (
    <form
      onSubmit={submit}
      className="flex flex-col gap-4 rounded-lg border border-border bg-surface-2/50 p-5"
    >
      {error && <p className="text-sm text-danger">{error}</p>}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <Input
          label="Nombre del canal"
          value={nombre}
          onChange={(e) => setNombre(e.target.value)}
          placeholder="Ej. Indie Vibes Weekly"
          required
        />
        <div className="flex flex-col gap-1.5">
          <label htmlFor="medio-tipo" className="text-sm font-medium text-text-muted">
            Tipo de canal
          </label>
          <select
            id="medio-tipo"
            value={tipo}
            onChange={(e) => setTipo(e.target.value)}
            className={cn(
              "h-[42px] w-full rounded-md border border-border bg-surface-2 px-3 text-sm text-text",
              "transition-all focus:outline-none focus:border-primary focus:ring-2 focus:ring-[var(--accent-glow)]",
              !tipo && "text-text-muted",
            )}
          >
            <option value="" disabled>
              Selecciona…
            </option>
            {MEDIO_TYPES.map((t) => (
              <option key={t.value} value={t.value} className="text-text">
                {t.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <Input
          label="URL (opcional)"
          type="url"
          value={url ?? ""}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://…"
        />
        <Input
          label="Audiencia estimada (opcional)"
          type="number"
          min={0}
          value={audiencia}
          onChange={(e) => setAudiencia(e.target.value)}
          placeholder="Ej. 12000"
        />
      </div>

      <Input
        label="Descripción (opcional)"
        value={descripcion ?? ""}
        onChange={(e) => setDescripcion(e.target.value)}
        placeholder="¿De qué trata tu canal?"
      />

      <div className="flex flex-col gap-2">
        <span className="text-sm font-medium text-text-muted">
          Géneros que cubre este canal
        </span>
        <div className="flex flex-wrap gap-2">
          {generos.map((g) => (
            <GenreChip
              key={g.id}
              label={g.nombre}
              size="sm"
              selected={generoIds.includes(g.id)}
              onToggle={() => toggleGenero(g.id)}
            />
          ))}
        </div>
      </div>

      <div className="flex justify-end gap-2">
        {onCancel && (
          <Button type="button" variant="ghost" onClick={onCancel}>
            Cancelar
          </Button>
        )}
        <Button type="submit" loading={submitting}>
          {submitLabel}
        </Button>
      </div>
    </form>
  );
}
