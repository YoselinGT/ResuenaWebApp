"use client";

/**
 * Confirmación de correo. Se ejecuta en cliente a propósito: el backend
 * responde con Set-Cookie (sesión post-confirmación) y sólo el navegador puede
 * persistir esa cookie. Tras confirmar, redirige a `siguiente` (onboarding o
 * /aplicar según el tipo de usuario).
 */

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Loader2 } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import { AuthCard } from "@/components/auth/AuthCard";
import { Button } from "@/components/ui/Button";

type ConfirmResponse = { mensaje: string; siguiente: string };
type State =
  | { kind: "loading" }
  | { kind: "ok"; siguiente: string }
  | { kind: "error"; title: string; message: string };

export default function ConfirmPage({
  params,
}: {
  params: { token: string };
}) {
  const router = useRouter();
  const [state, setState] = useState<State>({ kind: "loading" });
  const ran = useRef(false);

  useEffect(() => {
    // React 18 StrictMode monta dos veces en dev; el token es de un solo uso,
    // así que sólo disparamos la confirmación una vez.
    if (ran.current) return;
    ran.current = true;

    (async () => {
      try {
        const res = await api.get<ConfirmResponse>(
          `/auth/confirm/${encodeURIComponent(params.token)}`,
        );
        setState({ kind: "ok", siguiente: res.siguiente });
        setTimeout(() => router.replace(res.siguiente), 1400);
      } catch (err) {
        if (err instanceof ApiError && err.status === 410) {
          setState({
            kind: "error",
            title: "El enlace expiró",
            message:
              "Este enlace de confirmación ya no es válido. Regístrate de nuevo para recibir uno nuevo.",
          });
        } else if (err instanceof ApiError && err.status === 400) {
          setState({
            kind: "error",
            title: "Enlace inválido",
            message:
              "Este enlace no es válido o ya fue utilizado. Si ya confirmaste, inicia sesión.",
          });
        } else {
          setState({
            kind: "error",
            title: "No pudimos confirmar",
            message:
              err instanceof ApiError
                ? err.message
                : "Ocurrió un error. Reintenta más tarde.",
          });
        }
      }
    })();
  }, [params.token, router]);

  if (state.kind === "loading") {
    return (
      <AuthCard title="Confirmando tu cuenta…">
        <div className="flex flex-col items-center gap-3 py-4 text-text-muted">
          <Loader2 className="animate-spin text-primary-light" size={32} />
          <p className="text-sm">Un momento, validando tu enlace.</p>
        </div>
      </AuthCard>
    );
  }

  if (state.kind === "ok") {
    return (
      <AuthCard title="¡Cuenta confirmada!">
        <div className="flex flex-col items-center text-center">
          <div
            className="auth-success-check mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-success/15 text-3xl text-success"
            aria-hidden
          >
            ✓
          </div>
          <p className="text-sm text-text-muted">
            Tu correo quedó verificado. Te llevamos a completar tu perfil…
          </p>
          <Button className="mt-6" onClick={() => router.replace(state.siguiente)}>
            Continuar ahora
          </Button>
        </div>
      </AuthCard>
    );
  }

  return (
    <AuthCard title={state.title}>
      <div className="flex flex-col items-center gap-5 text-center">
        <p className="text-sm text-text-muted">{state.message}</p>
        <div className="flex gap-3">
          <Link href="/login">
            <Button variant="secondary">Iniciar sesión</Button>
          </Link>
          <Link href="/registro/artista">
            <Button variant="ghost">Registrarme</Button>
          </Link>
        </div>
      </div>
    </AuthCard>
  );
}
