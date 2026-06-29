"use client";

import { useEffect, useState } from "react";
import {
  ClipboardCheck,
  Coins,
  Inbox,
  Sparkles,
  type LucideIcon,
} from "lucide-react";
import { api } from "@/lib/api";
import {
  useDashboardUser,
  type TipoUsuario,
} from "@/components/layout/DashboardProvider";

type KpiConfig = { label: string; Icon: LucideIcon; hint: string };

// KPI principal por tipo de usuario. Los módulos que alimentan estos valores
// llegan en fases posteriores; por ahora se muestra un placeholder (0).
const KPI: Record<TipoUsuario, KpiConfig> = {
  artista: {
    label: "Créditos disponibles",
    Icon: Coins,
    hint: "Compra créditos para lanzar tus campañas.",
  },
  curador: {
    label: "Campañas pendientes",
    Icon: Inbox,
    hint: "Aquí verás las campañas que te lleguen para evaluar.",
  },
  admin: {
    label: "Solicitudes pendientes",
    Icon: ClipboardCheck,
    hint: "Revisa y aprueba las solicitudes de curadores.",
  },
};

export default function HomePage() {
  const user = useDashboardUser();
  const [mensaje, setMensaje] = useState<string | null>(null);

  useEffect(() => {
    api
      .get<{ mensaje_bienvenida: string }>("/config/public")
      .then((c) => setMensaje(c.mensaje_bienvenida))
      .catch(() => setMensaje(null));
  }, []);

  const primerNombre = user.nombre_completo.split(/\s+/)[0];
  const kpi = KPI[user.tipo] ?? KPI.artista;

  return (
    <div className="mx-auto flex w-full max-w-5xl flex-col gap-8">
      <header className="auth-enter">
        <h1 className="text-2xl font-bold tracking-tight text-text sm:text-3xl">
          Hola, {primerNombre} 👋
        </h1>
        <p className="mt-2 max-w-xl text-sm leading-relaxed text-text-muted">
          {mensaje ?? "Bienvenido de vuelta a Resuena."}
        </p>
      </header>

      <section className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {/* KPI principal según tipo */}
        <article className="rounded-lg border border-border bg-surface p-5 shadow-glow">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-text-muted">{kpi.label}</p>
            <span className="flex h-9 w-9 items-center justify-center rounded-md bg-primary/15 text-primary-light">
              <kpi.Icon size={18} />
            </span>
          </div>
          <p className="mt-3 text-3xl font-bold text-text tabular-nums">0</p>
          <p className="mt-1 text-xs text-text-muted">{kpi.hint}</p>
        </article>

        {/* Tarjeta de "próximamente" */}
        <article className="flex flex-col justify-center rounded-lg border border-dashed border-border bg-surface/40 p-5 sm:col-span-1 lg:col-span-2">
          <div className="flex items-center gap-2 text-primary-light">
            <Sparkles size={18} />
            <p className="text-sm font-semibold">Tu actividad aparecerá aquí</p>
          </div>
          <p className="mt-1.5 text-sm text-text-muted">
            A medida que uses Resuena, este panel mostrará tus campañas, métricas
            y novedades. Mientras tanto, completa tu perfil para sacarle el máximo.
          </p>
        </article>
      </section>
    </div>
  );
}
