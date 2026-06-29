"use client";

import { useRef, useState } from "react";
import { Camera, Trash2 } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import { Avatar } from "@/components/ui/Avatar";
import { Button } from "@/components/ui/Button";

type Props = {
  name: string;
  fotoUrl: string | null;
  /** Notifica al padre la nueva URL presigned (o null tras eliminar). */
  onChange: (fotoUrl: string | null) => void;
};

const ACCEPT = "image/jpeg";

export function PhotoUploader({ name, fotoUrl, onChange }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    e.target.value = ""; // permite re-seleccionar el mismo archivo
    if (!file) return;

    if (file.type !== ACCEPT) {
      setError("La foto debe ser una imagen JPEG.");
      return;
    }

    setError(null);
    setBusy(true);
    try {
      const form = new FormData();
      form.append("file", file);
      const res = await api.upload<{ foto_url: string | null }>(
        "/users/me/photo",
        form,
      );
      onChange(res.foto_url);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.status === 415
            ? "Formato no admitido. Sube una imagen JPEG."
            : err.message
          : "No se pudo subir la foto.",
      );
    } finally {
      setBusy(false);
    }
  }

  async function remove() {
    setError(null);
    setBusy(true);
    try {
      const res = await api.del<{ foto_url: string | null }>("/users/me/photo");
      onChange(res.foto_url);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo eliminar la foto.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex items-center gap-5">
      <Avatar name={name} src={fotoUrl} size={96} className="text-2xl" />

      <div className="flex flex-col gap-2">
        <div className="flex flex-wrap gap-2">
          <Button
            type="button"
            variant="secondary"
            size="sm"
            loading={busy}
            onClick={() => inputRef.current?.click()}
          >
            <Camera size={15} />
            {fotoUrl ? "Cambiar foto" : "Subir foto"}
          </Button>
          {fotoUrl && (
            <Button
              type="button"
              variant="ghost"
              size="sm"
              disabled={busy}
              onClick={remove}
            >
              <Trash2 size={15} />
              Eliminar
            </Button>
          )}
        </div>
        <p className="text-xs text-text-muted">JPEG, se recorta a 200×200.</p>
        {error && <p className="text-xs text-danger">{error}</p>}

        <input
          ref={inputRef}
          type="file"
          accept={ACCEPT}
          onChange={onFile}
          className="hidden"
          aria-hidden
        />
      </div>
    </div>
  );
}
