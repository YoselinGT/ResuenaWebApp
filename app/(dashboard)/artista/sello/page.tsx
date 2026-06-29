"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Building2, LogOut, Loader2, Mail, Plus } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Alert } from "@/components/ui/Alert";
import { Avatar } from "@/components/ui/Avatar";
import { useDashboardUser } from "@/components/layout/DashboardProvider";
import { CrearSelloModal, type Sello } from "@/components/sellos/CrearSelloModal";
import { MiembrosDelSello, type Miembro } from "@/components/sellos/MiembrosDelSello";

type SelloDetalle = Sello & { miembros: Miembro[] };

export default function SelloPage() {
  const router = useRouter();
  const user = useDashboardUser();
  const [sello, setSello] = useState<SelloDetalle | null>(null);
  const [loading, setLoading] = useState(true);
  const [showCrear, setShowCrear] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // invitación
  const [showInvitar, setShowInvitar] = useState(false);
  const [invCorreo, setInvCorreo] = useState("");
  const [invRol, setInvRol] = useState<"manager" | "artista">("artista");
  const [invMsg, setInvMsg] = useState<string | null>(null);
  const [invErr, setInvErr] = useState<string | null>(null);
  const [invLoading, setInvLoading] = useState(false);
  const [saliendo, setSaliendo] = useState(false);

  useEffect(() => {
    if (user.tipo !== "artista") router.replace("/home");
  }, [user.tipo, router]);

  const cargar = useCallback(async () => {
    try {
      setSello(await api.get<SelloDetalle | null>("/sellos/mio"));
      setError(null);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo cargar tu sello.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void cargar();
  }, [cargar]);

  async function invitar(e: React.FormEvent) {
    e.preventDefault();
    if (!sello) return;
    setInvErr(null);
    setInvMsg(null);
    setInvLoading(true);
    try {
      await api.post(`/sellos/${sello.id}/invitar`, {
        correo: invCorreo.trim(),
        rol: invRol,
      });
      setInvMsg(`Invitación enviada a ${invCorreo.trim()}.`);
      setInvCorreo("");
    } catch (err) {
      setInvErr(err instanceof ApiError ? err.message : "No se pudo invitar.");
    } finally {
      setInvLoading(false);
    }
  }

  async function salir() {
    if (!sello) return;
    setSaliendo(true);
    setError(null);
    try {
      await api.post(`/sellos/${sello.id}/salir`);
      setSello(null);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo salir del sello.");
    } finally {
      setSaliendo(false);
    }
  }

  if (loading) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center">
        <Loader2 className="animate-spin text-primary-light" size={32} />
      </div>
    );
  }

  const puedeGestionar = sello?.rol === "owner" || sello?.rol === "manager";

  return (
    <div className="mx-auto flex w-full max-w-3xl flex-col gap-6">
      <header>
        <h1 className="text-2xl font-bold tracking-tight text-text">Mi sello</h1>
        <p className="mt-1 text-sm text-text-muted">
          Gestiona tu sello discográfico y sus artistas.
        </p>
      </header>

      {error && <Alert variant="error">{error}</Alert>}

      {!sello ? (
        <section className="flex flex-col items-center rounded-lg border border-dashed border-border bg-surface/40 px-6 py-12 text-center">
          <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-primary/15 text-primary-light">
            <Building2 size={26} />
          </div>
          <h2 className="text-lg font-semibold text-text">Aún no tienes un sello</h2>
          <p className="mt-1.5 max-w-md text-sm text-text-muted">
            Crea tu propio sello para gestionar a otros artistas, o únete a uno
            existente desde el enlace de invitación que recibas por correo.
          </p>
          <Button className="mt-6" onClick={() => setShowCrear(true)}>
            <Plus size={16} />
            Crear mi sello
          </Button>
        </section>
      ) : (
        <>
          <section className="flex items-center gap-4 rounded-lg border border-border bg-surface p-5 shadow-glow">
            <Avatar name={sello.nombre} src={sello.logo_url} size={64} className="text-xl" />
            <div className="min-w-0 flex-1">
              <h2 className="truncate text-xl font-bold text-text">{sello.nombre}</h2>
              {sello.descripcion && (
                <p className="mt-0.5 truncate text-sm text-text-muted">
                  {sello.descripcion}
                </p>
              )}
              {sello.website && (
                <a
                  href={sello.website}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs text-primary-light hover:underline"
                >
                  {sello.website}
                </a>
              )}
            </div>
            <span className="rounded-full bg-primary/15 px-3 py-1 text-xs text-primary-light">
              {sello.rol}
            </span>
          </section>

          <section className="flex flex-col gap-3">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold text-text">
                Miembros ({sello.miembros.length})
              </h3>
              {puedeGestionar && (
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => {
                    setShowInvitar((v) => !v);
                    setInvMsg(null);
                    setInvErr(null);
                  }}
                >
                  <Mail size={15} />
                  Invitar artista
                </Button>
              )}
            </div>

            {showInvitar && puedeGestionar && (
              <form
                onSubmit={invitar}
                className="flex flex-col gap-3 rounded-lg border border-border bg-surface-2/50 p-4 sm:flex-row sm:items-end"
              >
                <div className="flex-1">
                  <Input
                    label="Correo del artista"
                    type="email"
                    required
                    value={invCorreo}
                    onChange={(e) => setInvCorreo(e.target.value)}
                    placeholder="artista@correo.com"
                  />
                </div>
                <div className="flex flex-col gap-1.5 sm:w-40">
                  <label htmlFor="inv-rol" className="text-sm font-medium text-text-muted">
                    Rol
                  </label>
                  <select
                    id="inv-rol"
                    value={invRol}
                    onChange={(e) => setInvRol(e.target.value as "manager" | "artista")}
                    className={cn(
                      "h-[42px] rounded-md border border-border bg-surface-2 px-3 text-sm text-text",
                      "focus:outline-none focus:border-primary focus:ring-2 focus:ring-[var(--accent-glow)]",
                    )}
                  >
                    <option value="artista">Artista</option>
                    <option value="manager">Manager</option>
                  </select>
                </div>
                <Button type="submit" loading={invLoading}>
                  Enviar
                </Button>
              </form>
            )}
            {invMsg && <Alert variant="success">{invMsg}</Alert>}
            {invErr && <Alert variant="error">{invErr}</Alert>}

            <MiembrosDelSello
              selloId={sello.id}
              miembros={sello.miembros}
              miRol={sello.rol ?? "artista"}
              onChanged={cargar}
            />
          </section>

          <div>
            <Button variant="ghost" onClick={salir} loading={saliendo}>
              <LogOut size={16} />
              Salir del sello
            </Button>
          </div>
        </>
      )}

      {showCrear && (
        <CrearSelloModal
          onClose={() => setShowCrear(false)}
          onCreated={(s) => {
            setShowCrear(false);
            void cargar();
          }}
        />
      )}
    </div>
  );
}
