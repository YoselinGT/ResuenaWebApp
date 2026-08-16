"use client";

import { useState, useEffect, useCallback } from "react";
import { Loader2 } from "lucide-react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Alert } from "@/components/ui/Alert";
import { GenerosCategoriasPicker } from "@/components/forms/GenerosCategoriasPicker";

type Categoria = {
  id: number;
  nombre: string;
  activo: boolean;
};

type Genero = {
  id: number;
  nombre: string;
  categorias: Categoria[];
};

export function CategoriasPerfilCard() {
  const [generos, setGeneros] = useState<Genero[]>([]);
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [ok, setOk] = useState(false);

  const loadData = useCallback(async () => {
    try {
      const [g, cats] = await Promise.all([
        api.get<Genero[]>("/generos"),
        api.get<Categoria[]>("/profesional/categorias"),
      ]);
      setGeneros(g);
      setSelectedIds(cats.map((c) => c.id));
      setError(null);
    } catch {
      setError("No se pudieron cargar las categorías.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    setOk(false);
    try {
      await api.put("/profesional/categorias", {
        categoria_ids: selectedIds,
      });
      setOk(true);
    } catch {
      setError("No se pudieron guardar las categorías.");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <section className="rounded-lg border border-border bg-surface p-6">
        <h2 className="text-base font-semibold text-text mb-4">
          Tus especialidades
        </h2>
        <div className="flex items-center justify-center py-8">
          <Loader2 className="animate-spin text-primary-light" size={24} />
        </div>
      </section>
    );
  }

  return (
    <section className="rounded-lg border border-border bg-surface p-6">
      <h2 className="text-base font-semibold text-text">
        Tus especialidades
      </h2>
      <p className="mt-1 text-sm text-text-muted">
        Selecciona los géneros y categorías que cubres. Esto ayuda a que te
        lleguen campañas relevantes.
      </p>

      <div className="mt-4 flex flex-col gap-4">
        {error && <Alert variant="error">{error}</Alert>}
        {ok && <Alert variant="success">Especialidades actualizadas.</Alert>}

        <GenerosCategoriasPicker
          generos={generos}
          selectedIds={selectedIds}
          onChange={setSelectedIds}
        />

        <div className="flex justify-end">
          <Button onClick={handleSave} loading={saving}>
            Guardar especialidades
          </Button>
        </div>
      </div>
    </section>
  );
}
