"use client";

import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Alert } from "@/components/ui/Alert";
import { PhotoUploader } from "@/components/forms/PhotoUploader";
import { SelloPerfilCard } from "@/components/sellos/SelloPerfilCard";
import { MediosPerfilCard } from "@/components/curador/MediosPerfilCard";
import { cn } from "@/lib/utils";

type UserMe = {
  id: string;
  nombre_completo: string;
  correo: string;
  tipo: "artista" | "curador" | "admin";
  activo: boolean;
  foto_url: string | null;
  estado_curador: string | null;
};

const TIPO_LABEL: Record<string, string> = {
  artista: "Artista",
  curador: "Curador",
  admin: "Administrador",
};

const ESTADO: Record<
  string,
  { label: string; cls: string }
> = {
  pendiente: { label: "En revisión", cls: "bg-warning/15 text-warning" },
  aprobada: { label: "Aprobada", cls: "bg-success/15 text-success" },
  rechazada: { label: "Rechazada", cls: "bg-danger/15 text-danger" },
};

export default function MiPerfilPage() {
  const [user, setUser] = useState<UserMe | null>(null);
  const [nombre, setNombre] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [ok, setOk] = useState(false);

  useEffect(() => {
    api
      .get<UserMe>("/users/me")
      .then((u) => {
        setUser(u);
        setNombre(u.nombre_completo);
      })
      .catch(() => setError("No se pudo cargar tu perfil."))
      .finally(() => setLoading(false));
  }, []);

  async function save(e: React.FormEvent) {
    e.preventDefault();
    if (!user) return;
    setError(null);
    setOk(false);
    setSaving(true);
    try {
      const updated = await api.patch<UserMe>("/users/me", {
        nombre_completo: nombre.trim(),
      });
      setUser(updated);
      setNombre(updated.nombre_completo);
      setOk(true);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo guardar.");
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center">
        <Loader2 className="animate-spin text-primary-light" size={32} />
      </div>
    );
  }

  if (!user) {
    return (
      <div className="mx-auto max-w-2xl">
        <Alert variant="error">{error ?? "No se pudo cargar tu perfil."}</Alert>
      </div>
    );
  }

  const cambiado = nombre.trim() !== user.nombre_completo;
  const estado = user.estado_curador ? ESTADO[user.estado_curador] : null;

  return (
    <div className="mx-auto flex w-full max-w-2xl flex-col gap-6">
      <header>
        <h1 className="text-2xl font-bold tracking-tight text-text">Mi perfil</h1>
        <p className="mt-1 text-sm text-text-muted">
          Gestiona tu foto y tus datos personales.
        </p>
      </header>

      <section className="rounded-lg border border-border bg-surface p-6 shadow-glow">
        <PhotoUploader
          name={user.nombre_completo}
          fotoUrl={user.foto_url}
          onChange={(foto_url) => setUser({ ...user, foto_url })}
        />
      </section>

      <form
        onSubmit={save}
        className="flex flex-col gap-4 rounded-lg border border-border bg-surface p-6"
      >
        {error && <Alert variant="error">{error}</Alert>}
        {ok && <Alert variant="success">Perfil actualizado.</Alert>}

        <Input
          label="Nombre completo"
          value={nombre}
          onChange={(e) => {
            setNombre(e.target.value);
            setOk(false);
          }}
          required
          minLength={2}
          maxLength={255}
        />

        <Input label="Correo electrónico" value={user.correo} readOnly disabled />

        <div className="flex flex-col gap-1.5">
          <span className="text-sm font-medium text-text-muted">
            Tipo de cuenta
          </span>
          <span className="inline-flex w-fit rounded-full bg-primary/15 px-3 py-1 text-sm text-primary-light">
            {TIPO_LABEL[user.tipo] ?? user.tipo}
          </span>
        </div>

        <div className="flex justify-end">
          <Button type="submit" loading={saving} disabled={!cambiado || !nombre.trim()}>
            Guardar cambios
          </Button>
        </div>
      </form>

      {user.tipo === "curador" && (
        <section className="rounded-lg border border-border bg-surface p-6">
          <h2 className="text-base font-semibold text-text">
            Estado de tu solicitud
          </h2>
          <p className="mt-1 text-sm text-text-muted">
            El equipo de Resuena revisa las solicitudes de curador.
          </p>
          <div className="mt-3">
            {estado ? (
              <span
                className={cn(
                  "inline-flex rounded-full px-3 py-1 text-sm font-medium",
                  estado.cls,
                )}
              >
                {estado.label}
              </span>
            ) : (
              <span className="text-sm text-text-muted">
                Aún no has enviado tu solicitud.
              </span>
            )}
          </div>
        </section>
      )}

      {user.tipo === "artista" && <SelloPerfilCard />}
      {user.tipo === "curador" && <MediosPerfilCard />}
    </div>
  );
}
