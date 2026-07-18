"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Loader2, Plus } from "lucide-react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Alert } from "@/components/ui/Alert";
import { useDashboardUser } from "@/components/layout/DashboardProvider";
import { MedioCard, type Medio } from "@/components/curador/MedioCard";
import { MedioFormModal } from "@/components/curador/MedioFormModal";
import type { Genero } from "@/components/onboarding/MedioForm";

export default function CuradorMediosPage() {
  const router = useRouter();
  const user = useDashboardUser();
  const [medios, setMedios] = useState<Medio[]>([]);
  const [generos, setGeneros] = useState<Genero[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [modalAbierto, setModalAbierto] = useState(false);
  const [editando, setEditando] = useState<Medio | null>(null);

  useEffect(() => {
    if (user.tipo !== "curador") router.replace("/home");
  }, [user.tipo, router]);

  useEffect(() => {
    Promise.all([
      api.get<Medio[]>("/curador/medios"),
      api.get<Genero[]>("/catalogos/generos"),
    ])
      .then(([m, g]) => {
        setMedios(m);
        setGeneros(g);
      })
      .catch(() => setError("No se pudieron cargar tus medios."))
      .finally(() => setLoading(false));
  }, []);

  const generosMap: Record<number, string> = Object.fromEntries(
    generos.map((g) => [g.id, g.nombre]),
  );

  function upsert(medio: Medio) {
    setMedios((prev) => {
      const i = prev.findIndex((m) => m.id === medio.id);
      if (i === -1) return [...prev, medio];
      const copy = [...prev];
      copy[i] = medio;
      return copy;
    });
  }

  if (loading) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center">
        <Loader2 className="animate-spin text-primary-light" size={32} />
      </div>
    );
  }

  return (
    <div className="mx-auto flex w-full max-w-5xl flex-col gap-6">
      <header className="flex items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-text">Mis medios</h1>
          <p className="mt-1 text-sm text-text-muted">
            Tus canales para recibir campañas. Cada uno funciona de forma independiente.
          </p>
        </div>
        <Button
          onClick={() => {
            setEditando(null);
            setModalAbierto(true);
          }}
        >
          <Plus size={16} />
          Añadir medio
        </Button>
      </header>

      {error && <Alert variant="error">{error}</Alert>}

      {medios.length > 0 &&
        medios.every((m) => m.estado_revision !== "aprobado") && (
          <Alert variant="warning">
            Aún no tienes canales aprobados. Puedes crear canales y explorar la
            plataforma, pero podrás aceptar campañas una vez que el equipo apruebe
            al menos uno.
          </Alert>
        )}

      {medios.length === 0 ? (
        <div className="rounded-lg border border-dashed border-border px-6 py-12 text-center text-sm text-text-muted">
          Aún no tienes medios. Añade tu primer canal para empezar a recibir campañas.
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {medios.map((m) => (
            <MedioCard
              key={m.id}
              medio={m}
              generosMap={generosMap}
              onChanged={upsert}
              onEdit={(medio) => {
                setEditando(medio);
                setModalAbierto(true);
              }}
            />
          ))}
        </div>
      )}

      {modalAbierto && (
        <MedioFormModal
          generos={generos}
          initial={editando}
          onClose={() => setModalAbierto(false)}
          onSaved={(medio) => {
            upsert(medio);
            setModalAbierto(false);
          }}
        />
      )}
    </div>
  );
}
