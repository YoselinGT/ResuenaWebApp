"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Link2 } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import { AuthCard } from "@/components/auth/AuthCard";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Alert } from "@/components/ui/Alert";
import { cn } from "@/lib/utils";

const TIPOS = [
  { value: "blogger", label: "Blogger / medio editorial" },
  { value: "playlister", label: "Playlister / curador de playlists" },
  { value: "influencer", label: "Influencer / redes sociales" },
  { value: "reels", label: "Creador de reels / video" },
  { value: "radio", label: "Radio / podcast" },
  { value: "otro", label: "Otro" },
];

export default function AplicarPage() {
  const router = useRouter();
  const [tipo, setTipo] = useState("");
  const [portfolio, setPortfolio] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    if (!tipo) {
      setError("Selecciona el tipo de profesional que eres.");
      return;
    }

    setLoading(true);
    try {
      await api.post("/auth/aplicar", {
        tipo_profesional: tipo,
        url_portfolio: portfolio.trim() || null,
      });
      router.push("/pendiente");
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        // Ya tiene una solicitud en revisión.
        router.push("/pendiente");
        return;
      }
      if (err instanceof ApiError && err.status === 401) {
        setError("Tu sesión expiró. Inicia sesión para continuar.");
      } else if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Ocurrió un error. Reintenta.");
      }
      setLoading(false);
    }
  }

  return (
    <AuthCard
      title="Cuéntanos sobre ti"
      subtitle="Completa tu solicitud para que el equipo de Resuena revise tu perfil de curador."
    >
      <form onSubmit={onSubmit} className="flex flex-col gap-5" noValidate>
        {error && <Alert variant="error">{error}</Alert>}

        <fieldset className="flex flex-col gap-2">
          <legend className="mb-1 text-sm font-medium text-text-muted">
            ¿Qué tipo de profesional eres?
          </legend>
          <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
            {TIPOS.map((t) => (
              <button
                key={t.value}
                type="button"
                onClick={() => setTipo(t.value)}
                aria-pressed={tipo === t.value}
                className={cn(
                  "rounded-md border px-3.5 py-3 text-left text-sm transition-all",
                  tipo === t.value
                    ? "border-primary bg-primary/10 text-text shadow-glow"
                    : "border-border bg-surface-2 text-text-muted hover:border-primary/40 hover:text-text",
                )}
              >
                {t.label}
              </button>
            ))}
          </div>
        </fieldset>

        <Input
          label="Enlace a tu portafolio (opcional)"
          type="url"
          value={portfolio}
          onChange={(e) => setPortfolio(e.target.value)}
          leftIcon={<Link2 size={16} />}
          placeholder="https://tu-blog.com, perfil de Spotify, etc."
          hint="Comparte tu blog, playlist o redes para agilizar la revisión."
        />

        <Button type="submit" loading={loading} fullWidth>
          Enviar solicitud
        </Button>
      </form>
    </AuthCard>
  );
}
