"use client";

import { useState } from "react";
import { Plus } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { GenreChip } from "@/components/onboarding/GenreChip";
import {
  RedSocialEditableRow,
  type RedEditable,
} from "@/components/onboarding/RedSocialEditableRow";
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
  descripcion: string | null;
  audiencia_estimada: number | null;
  precio_creditos: number;
  descripcion_precio: string | null;
  genero_ids: number[];
  redes: RedEditable[];
};

type MedioFormProps = {
  generos: Genero[];
  initial?: Partial<MedioFormValues>;
  submitting?: boolean;
  submitLabel?: string;
  onSubmit: (values: MedioFormValues) => void;
  onCancel?: () => void;
};

const EMPTY_RED: RedEditable = { tipo: "", url: "", es_principal: false };

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
  const [descripcion, setDescripcion] = useState(initial?.descripcion ?? "");
  const [audiencia, setAudiencia] = useState(
    initial?.audiencia_estimada != null ? String(initial.audiencia_estimada) : "",
  );
  const [precioCreditos, setPrecioCreditos] = useState(
    initial?.precio_creditos != null ? String(initial.precio_creditos) : "1",
  );
  const [descripcionPrecio, setDescripcionPrecio] = useState(
    initial?.descripcion_precio ?? "",
  );
  const [generoIds, setGeneroIds] = useState<number[]>(initial?.genero_ids ?? []);
  const [redes, setRedes] = useState<RedEditable[]>(
    initial?.redes?.length
      ? initial.redes
      : [{ tipo: "", url: "", es_principal: true }],
  );
  const [error, setError] = useState<string | null>(null);

  function toggleGenero(id: number) {
    setGeneroIds((prev) =>
      prev.includes(id) ? prev.filter((g) => g !== id) : [...prev, id],
    );
  }

  function addRed() {
    setRedes((prev) => [...prev, { ...EMPTY_RED }]);
  }

  function removeRed(index: number) {
    setRedes((prev) => {
      const next = prev.filter((_, i) => i !== index);
      // Si eliminamos la principal, marcar la primera como principal
      if (prev[index].es_principal && next.length > 0) {
        next[0] = { ...next[0], es_principal: true };
      }
      return next.length > 0 ? next : [{ ...EMPTY_RED, es_principal: true }];
    });
  }

  function updateRed(index: number, updated: RedEditable) {
    setRedes((prev) => prev.map((r, i) => (i === index ? updated : r)));
  }

  function setPrincipal(index: number) {
    setRedes((prev) =>
      prev.map((r, i) => ({ ...r, es_principal: i === index })),
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

    // Validar redes
    const redesValidas = redes.filter((r) => r.tipo && r.url.trim());
    if (redesValidas.length === 0) {
      setError("Agrega al menos una red social con tipo y URL.");
      return;
    }
    // Asegurar que hay una principal
    if (!redesValidas.some((r) => r.es_principal)) {
      redesValidas[0].es_principal = true;
    }

    const precio = parseInt(precioCreditos, 10);
    if (isNaN(precio) || precio < 1) {
      setError("El precio debe ser al menos 1 crédito.");
      return;
    }

    setError(null);
    onSubmit({
      nombre: nombre.trim(),
      tipo,
      descripcion: descripcion.trim() || null,
      audiencia_estimada: audiencia ? Number(audiencia) : null,
      precio_creditos: precio,
      descripcion_precio: descripcionPrecio.trim() || null,
      genero_ids: generoIds,
      redes: redesValidas,
    });
  }

  return (
    <form
      onSubmit={submit}
      className="flex flex-col gap-4 rounded-lg border border-border bg-surface-2/50 p-5"
    >
      {error && <p className="text-sm text-danger">{error}</p>}

      {/* Nombre + Tipo */}
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

      {/* Descripción + Audiencia */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <Input
          label="Descripción (opcional)"
          value={descripcion ?? ""}
          onChange={(e) => setDescripcion(e.target.value)}
          placeholder="¿De qué trata tu canal?"
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

      {/* Redes sociales del canal */}
      <div className="flex flex-col gap-2">
        <span className="text-sm font-medium text-text-muted">
          Redes sociales de este canal
        </span>
        <div className="flex flex-col gap-2">
          {redes.map((r, i) => (
            <RedSocialEditableRow
              key={i}
              red={r}
              index={i}
              total={redes.length}
              onChange={(updated) => updateRed(i, updated)}
              onRemove={() => removeRed(i)}
              onSetPrincipal={() => setPrincipal(i)}
            />
          ))}
        </div>
        <Button
          type="button"
          variant="ghost"
          size="sm"
          onClick={addRed}
          className="self-start"
        >
          <Plus size={14} /> Agregar otra red
        </Button>
      </div>

      {/* Precio y géneros */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <Input
          label="Precio (créditos por campaña)"
          type="number"
          min={1}
          value={precioCreditos}
          onChange={(e) => setPrecioCreditos(e.target.value)}
          placeholder="1"
          required
        />
        <Input
          label="Descripción del precio (opcional)"
          value={descripcionPrecio ?? ""}
          onChange={(e) => setDescripcionPrecio(e.target.value)}
          placeholder="Ej. Reel de 15–60 segundos"
        />
      </div>

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
