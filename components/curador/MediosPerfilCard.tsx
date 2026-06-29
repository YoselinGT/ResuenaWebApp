"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ChevronRight } from "lucide-react";

import { api } from "@/lib/api";

type Medio = { id: string; nombre: string; tipo: string; activo: boolean };

/** Sección compacta de medios para el perfil del curador (T24). */
export function MediosPerfilCard() {
  const [medios, setMedios] = useState<Medio[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get<Medio[]>("/curador/medios")
      .then(setMedios)
      .catch(() => setMedios([]))
      .finally(() => setLoading(false));
  }, []);

  return (
    <section className="rounded-lg border border-border bg-surface p-6">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-base font-semibold text-text">Mis medios</h2>
        <Link
          href="/curador/medios"
          className="inline-flex items-center gap-1 text-sm font-medium text-primary-light hover:underline"
        >
          Gestionar
          <ChevronRight size={15} />
        </Link>
      </div>

      {loading ? (
        <div className="credits-skeleton-shimmer h-10 rounded-md" />
      ) : medios.length === 0 ? (
        <p className="text-sm text-text-muted">
          Aún no tienes medios. Añádelos desde el panel de medios.
        </p>
      ) : (
        <ul className="flex flex-col gap-1.5">
          {medios.slice(0, 5).map((m) => (
            <li
              key={m.id}
              className="flex items-center justify-between rounded-md bg-surface-2 px-3 py-2 text-sm"
            >
              <span className="truncate text-text">{m.nombre}</span>
              <span className="ml-2 shrink-0 text-xs text-text-muted">
                {m.tipo}
                {!m.activo && " · inactivo"}
              </span>
            </li>
          ))}
          {medios.length > 5 && (
            <li className="px-3 pt-1 text-xs text-text-muted">
              y {medios.length - 5} más…
            </li>
          )}
        </ul>
      )}
    </section>
  );
}
