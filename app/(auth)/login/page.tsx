"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Eye, EyeOff, Lock, Mail } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import { AuthCard } from "@/components/auth/AuthCard";
import { OTPModal } from "@/components/auth/OTPModal";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Alert } from "@/components/ui/Alert";

type LoginResponse = { pre_auth_session_id: string };

function lockedMessage(iso: string): string {
  const until = new Date(iso);
  if (Number.isNaN(until.getTime())) {
    return "Tu cuenta está bloqueada temporalmente por seguridad. Inténtalo más tarde.";
  }
  const hora = until.toLocaleTimeString("es", {
    hour: "2-digit",
    minute: "2-digit",
  });
  return `Demasiados intentos fallidos. Tu cuenta está bloqueada hasta las ${hora}.`;
}

export default function LoginPage() {
  const router = useRouter();
  const [correo, setCorreo] = useState("");
  const [password, setPassword] = useState("");
  const [showPw, setShowPw] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res = await api.post<LoginResponse>("/auth/login", {
        correo,
        password,
      });
      setSessionId(res.pre_auth_session_id);
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.code === "LOCKED" || err.status === 423) {
          setError(lockedMessage(err.message));
        } else if (err.status === 403) {
          // Profesional sin aprobar o email sin confirmar.
          if (/revisi/i.test(err.message)) {
            router.push("/pendiente");
            return;
          }
          setError(err.message);
        } else if (err.status === 401) {
          setError("Correo o contraseña incorrectos.");
        } else {
          setError(err.message);
        }
      } else {
        setError("Ocurrió un error. Reintenta.");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <AuthCard
        title="Inicia sesión"
        subtitle="Bienvenido de vuelta a Resuena."
        footer={
          <>
            ¿No tienes cuenta?{" "}
            <Link
              href="/registro/artista"
              className="font-medium text-primary-light hover:underline"
            >
              Crea una
            </Link>
          </>
        }
      >
        <form onSubmit={onSubmit} className="flex flex-col gap-4" noValidate>
          {error && <Alert variant="error">{error}</Alert>}

          <Input
            label="Correo electrónico"
            type="email"
            autoComplete="email"
            required
            value={correo}
            onChange={(e) => setCorreo(e.target.value)}
            leftIcon={<Mail size={16} />}
            placeholder="tu@correo.com"
          />

          <Input
            label="Contraseña"
            type={showPw ? "text" : "password"}
            autoComplete="current-password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            leftIcon={<Lock size={16} />}
            placeholder="••••••••"
            rightSlot={
              <button
                type="button"
                onClick={() => setShowPw((v) => !v)}
                aria-label={showPw ? "Ocultar contraseña" : "Mostrar contraseña"}
                className="p-1.5 text-text-muted transition-colors hover:text-text"
              >
                {showPw ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            }
          />

          <div className="-mt-1 text-right">
            <Link
              href="/forgot"
              className="text-sm text-text-muted transition-colors hover:text-primary-light"
            >
              ¿Olvidaste tu contraseña?
            </Link>
          </div>

          <Button type="submit" loading={loading} fullWidth>
            Continuar
          </Button>
        </form>
      </AuthCard>

      {sessionId && (
        <OTPModal
          preAuthSessionId={sessionId}
          correo={correo}
          onClose={() => setSessionId(null)}
          onSuccess={() => router.push("/")}
        />
      )}
    </>
  );
}
