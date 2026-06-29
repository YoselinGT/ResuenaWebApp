"use client";

import { useState } from "react";
import Link from "next/link";
import { Eye, EyeOff, Lock, Mail, User } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import { isStrongPassword } from "@/lib/password";
import { AuthCard } from "@/components/auth/AuthCard";
import { PasswordStrengthMeter } from "@/components/auth/PasswordStrengthMeter";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Alert } from "@/components/ui/Alert";
import { SoundWave } from "@/components/ui/SoundWave";

type Tipo = "artista" | "profesional";

const COPY: Record<
  Tipo,
  { title: string; subtitle: string; switchHref: string; switchLabel: string }
> = {
  artista: {
    title: "Crea tu cuenta de artista",
    subtitle: "Lanza campañas y conecta con curadores de la industria.",
    switchHref: "/registro/profesional",
    switchLabel: "Soy curador / profesional",
  },
  profesional: {
    title: "Crea tu cuenta de profesional",
    subtitle:
      "Bloggers, playlisters, influencers y creadores: recibe campañas y entrega contenido.",
    switchHref: "/registro/artista",
    switchLabel: "Soy artista / sello",
  },
};

export function RegisterForm({ tipo }: { tipo: Tipo }) {
  const copy = COPY[tipo];
  const [nombre, setNombre] = useState("");
  const [correo, setCorreo] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [showPw, setShowPw] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    if (nombre.trim().length < 2) {
      setError("Ingresa tu nombre completo.");
      return;
    }
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
      await api.post(`/auth/register/${tipo}`, {
        nombre_completo: nombre.trim(),
        correo: correo.trim(),
        password,
      });
      setDone(true);
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        setError("Ya existe una cuenta con ese correo. ¿Quieres iniciar sesión?");
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
      <AuthCard title="Revisa tu correo" hideLogo>
        <div className="flex flex-col items-center text-center">
          <div className="auth-envelope mb-4 text-6xl" aria-hidden>
            ✉️
          </div>
          <p className="text-sm leading-relaxed text-text-muted">
            Enviamos un enlace de confirmación a{" "}
            <span className="font-medium text-text">{correo}</span>. Ábrelo para
            activar tu cuenta
            {tipo === "profesional"
              ? " y completar tu solicitud."
              : " y comenzar."}
          </p>
          <SoundWave className="my-6" height={30} />
          <p className="text-xs text-text-muted">
            ¿No lo ves? Revisa tu carpeta de spam.
          </p>
          <Link
            href="/login"
            className="mt-5 text-sm font-medium text-primary-light hover:underline"
          >
            Volver a iniciar sesión
          </Link>
        </div>
      </AuthCard>
    );
  }

  return (
    <AuthCard
      title={copy.title}
      subtitle={copy.subtitle}
      footer={
        <>
          ¿Ya tienes cuenta?{" "}
          <Link
            href="/login"
            className="font-medium text-primary-light hover:underline"
          >
            Inicia sesión
          </Link>
        </>
      }
    >
      <form onSubmit={onSubmit} className="flex flex-col gap-4" noValidate>
        {error && <Alert variant="error">{error}</Alert>}

        <Input
          label="Nombre completo"
          autoComplete="name"
          required
          value={nombre}
          onChange={(e) => setNombre(e.target.value)}
          leftIcon={<User size={16} />}
          placeholder="Tu nombre o el de tu proyecto"
        />

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

        <div className="flex flex-col gap-2">
          <Input
            label="Contraseña"
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
          Crear cuenta
        </Button>

        <Link
          href={copy.switchHref}
          className="text-center text-sm text-text-muted transition-colors hover:text-primary-light"
        >
          {copy.switchLabel}
        </Link>
      </form>
    </AuthCard>
  );
}
