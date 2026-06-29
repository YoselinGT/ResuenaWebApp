"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Loader2 } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import { Avatar } from "@/components/ui/Avatar";
import { Button } from "@/components/ui/Button";
import { Alert } from "@/components/ui/Alert";

type InvitacionDetalle = {
  sello_nombre: string;
  sello_logo_url: string | null;
  invitador: string | null;
  rol: string;
  estado: string;
  expires_at: string;
};

export default function InvitacionPage({
  params,
}: {
  params: { token: string };
}) {
  const router = useRouter();
  const [inv, setInv] = useState<InvitacionDetalle | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [accion, setAccion] = useState<"idle" | "aceptando" | "rechazando" | "rechazada">("idle");

  useEffect(() => {
    api
      .get<InvitacionDetalle>(`/sellos/invitacion/${encodeURIComponent(params.token)}`)
      .then(setInv)
      .catch((err) =>
        setError(
          err instanceof ApiError && err.status === 400
            ? "Esta invitación no es válida."
            : err instanceof ApiError
              ? err.message
              : "No se pudo cargar la invitación.",
        ),
      )
      .finally(() => setLoading(false));
  }, [params.token]);

  async function aceptar() {
    setAccion("aceptando");
    setError(null);
    try {
      await api.post(`/sellos/aceptar-invitacion/${encodeURIComponent(params.token)}`);
      router.push("/artista/sello");
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.status === 409
            ? "Ya perteneces a un sello. Sal de él antes de unirte a otro."
            : err.message
          : "No se pudo aceptar la invitación.",
      );
      setAccion("idle");
    }
  }

  async function rechazar() {
    setAccion("rechazando");
    setError(null);
    try {
      await api.post(`/sellos/rechazar-invitacion/${encodeURIComponent(params.token)}`);
      setAccion("rechazada");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo rechazar.");
      setAccion("idle");
    }
  }

  if (loading) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center">
        <Loader2 className="animate-spin text-primary-light" size={32} />
      </div>
    );
  }

  const Card = ({ children }: { children: React.ReactNode }) => (
    <div className="mx-auto mt-6 w-full max-w-md rounded-lg border border-border bg-surface p-7 text-center shadow-glow">
      {children}
    </div>
  );

  if (error && !inv) {
    return (
      <Card>
        <Alert variant="error">{error}</Alert>
        <Link href="/artista/sello" className="mt-5 inline-block text-sm text-primary-light hover:underline">
          Ir a mi sello
        </Link>
      </Card>
    );
  }

  if (!inv) return null;

  if (accion === "rechazada") {
    return (
      <Card>
        <p className="text-sm text-text-muted">
          Rechazaste la invitación a <strong className="text-text">{inv.sello_nombre}</strong>.
        </p>
        <Link href="/artista/sello" className="mt-5 inline-block text-sm text-primary-light hover:underline">
          Ir a mi sello
        </Link>
      </Card>
    );
  }

  const pendiente = inv.estado === "pendiente";

  return (
    <Card>
      <Avatar name={inv.sello_nombre} src={inv.sello_logo_url} size={72} className="mx-auto text-2xl" />
      <h1 className="mt-4 text-xl font-bold text-text">{inv.sello_nombre}</h1>
      <p className="mt-2 text-sm leading-relaxed text-text-muted">
        {inv.invitador ? <strong className="text-text">{inv.invitador}</strong> : "Un sello"}{" "}
        te invitó a unirte como{" "}
        <span className="font-medium text-primary-light">{inv.rol}</span>.
      </p>

      {error && (
        <div className="mt-4 text-left">
          <Alert variant="error">{error}</Alert>
        </div>
      )}

      {pendiente ? (
        <div className="mt-6 flex justify-center gap-3">
          <Button onClick={aceptar} loading={accion === "aceptando"} disabled={accion !== "idle"}>
            Aceptar
          </Button>
          <Button variant="ghost" onClick={rechazar} loading={accion === "rechazando"} disabled={accion !== "idle"}>
            Rechazar
          </Button>
        </div>
      ) : (
        <div className="mt-6">
          <Alert variant="info">
            {inv.estado === "expirada"
              ? "Esta invitación expiró."
              : inv.estado === "aceptada"
                ? "Esta invitación ya fue aceptada."
                : "Esta invitación ya no está disponible."}
          </Alert>
          <Link href="/artista/sello" className="mt-5 inline-block text-sm text-primary-light hover:underline">
            Ir a mi sello
          </Link>
        </div>
      )}
    </Card>
  );
}
