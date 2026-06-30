"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, Check, Loader2, X } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Alert } from "@/components/ui/Alert";
import { useDashboardUser } from "@/components/layout/DashboardProvider";
import { SolicitudCard, type Solicitud } from "@/components/admin/SolicitudCard";
import { RechazarModal } from "@/components/admin/RechazarModal";

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
  const [busy, setBusy] = useState(false);
  const [rechazar, setRechazar] = useState(false);

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

  async function aprobar() {
    setBusy(true);
    try {
      await api.post(`/admin/solicitudes/${params.id}/aprobar`);
      await cargar();
    } finally {
      setBusy(false);
    }
  }

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
        <ArrowLeft size={16} /> Volver
      </Link>

      {error || !sol ? (
        <Alert variant="error">{error ?? "Solicitud no encontrada."}</Alert>
      ) : (
        <>
          <SolicitudCard solicitud={sol} />
          {sol.estado === "pendiente" && (
            <div className="flex gap-3">
              <Button onClick={aprobar} loading={busy}>
                <Check size={16} /> Aprobar
              </Button>
              <Button variant="danger" disabled={busy} onClick={() => setRechazar(true)}>
                <X size={16} /> Rechazar
              </Button>
            </div>
          )}

          {rechazar && (
            <RechazarModal
              solicitudId={sol.id}
              nombre={sol.nombre_completo}
              onClose={() => setRechazar(false)}
              onRejected={() => {
                setRechazar(false);
                void cargar();
              }}
            />
          )}
        </>
      )}
    </div>
  );
}
