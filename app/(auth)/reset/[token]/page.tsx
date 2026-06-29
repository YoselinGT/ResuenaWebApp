"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Eye, EyeOff, Lock } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import { isStrongPassword } from "@/lib/password";
import { AuthCard } from "@/components/auth/AuthCard";
import { PasswordStrengthMeter } from "@/components/auth/PasswordStrengthMeter";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Alert } from "@/components/ui/Alert";

export default function ResetPage({ params }: { params: { token: string } }) {
  const router = useRouter();
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [showPw, setShowPw] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    if (!isStrongPassword(password)) {
      setError("La contraseña no cumple los requisitos de seguridad.");
      return;
    }
    if (password !== confirm) {
      setError("Las contraseñas no coinciden.");
      return;
    }

    setLoading(true);
    try {
      await api.post(
        `/auth/reset-password/${encodeURIComponent(params.token)}`,
        { password },
      );
      setDone(true);
    } catch (err) {
      if (err instanceof ApiError && err.status === 410) {
        setError("El enlace de recuperación expiró. Solicita uno nuevo.");
      } else if (err instanceof ApiError && err.status === 400) {
        setError("Este enlace no es válido o ya fue utilizado.");
      } else if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Ocurrió un error. Reintenta.");
      }
    } finally {
      setLoading(false);
    }
  }

  if (done) {
    return (
      <AuthCard title="Contraseña actualizada">
        <div className="flex flex-col items-center text-center">
          <div
            className="auth-success-check mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-success/15 text-3xl text-success"
            aria-hidden
          >
            ✓
          </div>
          <p className="text-sm text-text-muted">
            Tu contraseña se cambió correctamente. Ya puedes iniciar sesión.
          </p>
          <Button className="mt-6" onClick={() => router.push("/login")}>
            Iniciar sesión
          </Button>
        </div>
      </AuthCard>
    );
  }

  return (
    <AuthCard
      title="Nueva contraseña"
      subtitle="Elige una contraseña fuerte para tu cuenta."
      footer={
        <Link
          href="/login"
          className="font-medium text-primary-light hover:underline"
        >
          ← Volver a iniciar sesión
        </Link>
      }
    >
      <form onSubmit={onSubmit} className="flex flex-col gap-4" noValidate>
        {error && <Alert variant="error">{error}</Alert>}

        <div className="flex flex-col gap-2">
          <Input
            label="Nueva contraseña"
            type={showPw ? "text" : "password"}
            autoComplete="new-password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            leftIcon={<Lock size={16} />}
            placeholder="Crea una contraseña fuerte"
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
          <PasswordStrengthMeter password={password} />
        </div>

        <Input
          label="Confirma tu contraseña"
          type={showPw ? "text" : "password"}
          autoComplete="new-password"
          required
          value={confirm}
          onChange={(e) => setConfirm(e.target.value)}
          leftIcon={<Lock size={16} />}
          placeholder="Repite la contraseña"
          error={
            confirm.length > 0 && confirm !== password
              ? "Las contraseñas no coinciden."
              : null
          }
        />

        <Button type="submit" loading={loading} fullWidth className="mt-1">
          Cambiar contraseña
        </Button>
      </form>
    </AuthCard>
  );
}
