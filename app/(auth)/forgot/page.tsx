"use client";

import { useState } from "react";
import Link from "next/link";
import { Mail } from "lucide-react";
import { api } from "@/lib/api";
import { AuthCard } from "@/components/auth/AuthCard";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Alert } from "@/components/ui/Alert";

export default function ForgotPage() {
  const [correo, setCorreo] = useState("");
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    try {
      // El backend siempre responde 200 (no revela si el correo existe).
      await api.post("/auth/forgot-password", { correo: correo.trim() });
    } catch {
      // Aun ante error de red mostramos el mismo mensaje neutro.
    } finally {
      setLoading(false);
      setSent(true);
    }
  }

  if (sent) {
    return (
      <AuthCard title="Revisa tu correo">
        <div className="flex flex-col items-center text-center">
          <div className="auth-envelope mb-4 text-6xl" aria-hidden>
            ✉️
          </div>
          <p className="text-sm leading-relaxed text-text-muted">
            Si existe una cuenta asociada a{" "}
            <span className="font-medium text-text">{correo}</span>, te enviamos
            instrucciones para restablecer tu contraseña.
          </p>
          <Link
            href="/login"
            className="mt-6 text-sm font-medium text-primary-light hover:underline"
          >
            Volver a iniciar sesión
          </Link>
        </div>
      </AuthCard>
    );
  }

  return (
    <AuthCard
      title="¿Olvidaste tu contraseña?"
      subtitle="Ingresa tu correo y te enviaremos un enlace para restablecerla."
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
        <Alert variant="info">
          Por seguridad, siempre verás el mismo mensaje, exista o no la cuenta.
        </Alert>
        <Button type="submit" loading={loading} fullWidth>
          Enviar enlace
        </Button>
      </form>
    </AuthCard>
  );
}
