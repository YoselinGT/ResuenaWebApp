"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Loader2, Plus } from "lucide-react";
import { api } from "@/lib/api";
import { Alert } from "@/components/ui/Alert";
import { Button } from "@/components/ui/Button";
import { useDashboardUser } from "@/components/layout/DashboardProvider";
import { GenerosTable } from "@/components/admin/GenerosTable";
import { GeneroFormModal } from "@/components/admin/GeneroFormModal";

export type Categoria = {
  id: number;
  nombre: string;
  activo: boolean;
};

export type GeneroAdmin = {
  id: number;
  nombre: string;
  activo: boolean;
  categorias: Categoria[];
};

export default function AdminGenerosPage() {
  const router = useRouter();
  const user = useDashboardUser();
  const [generos, setGeneros] = useState<GeneroAdmin[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showModal, setShowModal] = useState(false);

  useEffect(() => {
    if (!user.es_admin) router.replace("/home");
  }, [user.es_admin, router]);

  const refreshGeneros = useCallback(async () => {
    try {
      const data = await api.get<GeneroAdmin[]>("/admin/generos");
      setGeneros(data);
      setError(null);
    } catch {
      setError("No se pudieron cargar los géneros.");
    }
  }, []);

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const data = await api.get<GeneroAdmin[]>("/admin/generos");
        if (!active) return;
        setGeneros(data);
        setError(null);
      } catch {
        if (active) setError("No se pudieron cargar los géneros.");
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => { active = false; };
  }, []);

  if (loading) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center">
        <Loader2 className="animate-spin text-primary-light" size={32} />
      </div>
    );
  }

  return (
    <div className="mx-auto flex w-full max-w-[900px] flex-col gap-5 px-4">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-text">
            Géneros musicales
          </h1>
          <p className="mt-1 text-sm text-text-muted">
            Gestiona los géneros y sus sub-categorías.
          </p>
        </div>
        <Button onClick={() => setShowModal(true)}>
          <Plus size={16} />
          Nuevo género
        </Button>
      </header>

      {error && <Alert variant="error">{error}</Alert>}

      <GenerosTable generos={generos} onRefresh={refreshGeneros} />

      {showModal && (
        <GeneroFormModal
          onClose={() => setShowModal(false)}
          onSaved={() => {
            setShowModal(false);
            refreshGeneros();
          }}
        />
      )}
    </div>
  );
}
