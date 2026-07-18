"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, Loader2 } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import { Alert } from "@/components/ui/Alert";
import { useDashboardUser } from "@/components/layout/DashboardProvider";
import {
  EstadoBadge,
  SolicitudCard,
  type Solicitud,
} from "@/components/admin/SolicitudCard";
import { CanalRevisionCard } from "@/components/admin/CanalRevisionCard";

export default function AdminSolicitudDetallePage({
  params,
}: {
  params: { id: string };
}) {
  const router = useRouter();
  const user = useDashboardUser();
  const [sol, setSol] = useState<Solicitud | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!user.es_admin) router.replace("/home");
  }, [user.es_admin, router]);

  const cargar = useCallback(async () => {
    try {
      setSol(await api.get<Solicitud>(`/admin/solicitudes/${params.id}`));
      setError(null);
    } catch (err) {
      setError(
        err instanceof ApiError && err.status === 404
          ? "Solicitud no encontrada."
          : "No se pudo cargar la solicitud.",
      );
    } finally {
      setLoading(false);
    }
  }, [params.id]);

  useEffect(() => {
    void cargar();
  }, [cargar]);

  if (loading) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center">
        <Loader2 className="animate-spin text-primary-light" size={32} />
      </div>
    );
  }

  return (
    <div className="mx-auto flex w-full max-w-2xl flex-col gap-5">
      <Link
        href="/admin/solicitudes"
        className="inline-flex items-center gap-1.5 text-sm text-text-muted hover:text-text"
      >
        <ArrowLeft size={16} /> Solicitudes
      </Link>

      {error || !sol ? (
        <Alert variant="error">{error ?? "Solicitud no encontrada."}</Alert>
      ) : (
        <>
          {/* Header de solicitud */}
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0">
              <h1 className="truncate text-xl font-bold text-text">
                {sol.nombre_completo}
              </h1>
              <p className="text-sm text-text-muted">
                {sol.correo} · Solicitó{" "}
                {new Date(sol.created_at).toLocaleDateString("es")}
              </p>
            </div>
            <EstadoBadge estado={sol.estado} />
          </div>

          {/* Canales para revisar */}
          <section>
            <h2 className="mb-3 text-sm font-medium uppercase tracking-wide text-text-muted">
              Canales para revisar
            </h2>
            {!sol.canales || sol.canales.length === 0 ? (
              <p className="rounded-md border border-dashed border-border px-4 py-6 text-center text-sm text-text-muted">
                El curador no ha registrado canales aún.
              </p>
            ) : (
              <div className="flex flex-col gap-3">
                {sol.canales.map((c) => (
                  <CanalRevisionCard
                    key={c.id}
                    canal={c}
                    solicitudPendiente={sol.estado === "pendiente"}
                    onAprobar={async () => {
                      await api.post(
                        `/admin/solicitudes/${sol.id}/canales/${c.id}/aprobar`,
                      );
                      await cargar();
                    }}
                    onRechazar={async (motivo: string) => {
                      await api.post(
                        `/admin/solicitudes/${sol.id}/canales/${c.id}/rechazar`,
                        { motivo },
                      );
                      await cargar();
                    }}
                    onRevertir={async () => {
                      await api.post(
                        `/admin/solicitudes/${sol.id}/canales/${c.id}/pendiente`,
                      );
                      await cargar();
                    }}
                  />
                ))}
              </div>
            )}
          </section>
        </>
      )}
    </div>
  );
}
