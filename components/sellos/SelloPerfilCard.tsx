"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Building2, ChevronRight } from "lucide-react";
import { api } from "@/lib/api";
import { Avatar } from "@/components/ui/Avatar";

type Sello = {
  id: string;
  nombre: string;
  logo_url: string | null;
  rol: string | null;
};

const ROL_LABEL: Record<string, string> = {
  owner: "Owner",
  manager: "Manager",
  artista: "Artista",
};

/** Sección de sello para el perfil del artista (T15). */
export function SelloPerfilCard() {
  const [sello, setSello] = useState<Sello | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get<Sello | null>("/sellos/mio")
      .then(setSello)
      .catch(() => setSello(null))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <section className="rounded-lg border border-border bg-surface p-6">
        <div className="credits-skeleton-shimmer h-12 rounded-md" />
      </section>
    );
  }

  return (
    <section className="rounded-lg border border-border bg-surface p-6">
      <h2 className="mb-3 text-base font-semibold text-text">Sello discográfico</h2>

      {sello ? (
        <Link
          href="/artista/sello"
          className="flex items-center gap-3 rounded-md border border-border bg-surface-2 px-4 py-3 transition-colors hover:border-primary/50"
        >
          <Avatar name={sello.nombre} src={sello.logo_url} size={40} />
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-medium text-text">
              Miembro de {sello.nombre}
            </p>
            <p className="text-xs text-text-muted">
              {ROL_LABEL[sello.rol ?? "artista"] ?? sello.rol}
            </p>
          </div>
          <ChevronRight size={18} className="shrink-0 text-text-muted" />
        </Link>
      ) : (
        <div className="flex items-center gap-3">
          <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-md bg-primary/15 text-primary-light">
            <Building2 size={18} />
          </span>
          <p className="flex-1 text-sm text-text-muted">
            No perteneces a ningún sello.
          </p>
          <Link
            href="/artista/sello"
            className="text-sm font-medium text-primary-light hover:underline"
          >
            Crear o unirse a un sello
          </Link>
        </div>
      )}
    </section>
  );
}
