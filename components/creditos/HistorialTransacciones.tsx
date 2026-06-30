"use client";

import { useCallback, useEffect, useState } from "react";
import { Loader2 } from "lucide-react";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/Button";

type Transaccion = {
  id: string;
  tipo: string;
  monto: number;
  descripcion: string | null;
  referencia_stripe: string | null;
  created_at: string;
};
type Paginated = {
  items: Transaccion[];
  total: number;
  page: number;
  page_size: number;
};

const PAGE_SIZE = 10;
// Tipos que suman (crédito) vs restan (débito).
const ES_CREDITO = new Set(["compra", "devolucion"]);

const TIPO_LABEL: Record<string, string> = {
  compra: "Compra",
  gasto: "Gasto",
  devolucion: "Devolución",
  retiro: "Retiro",
};

export function HistorialTransacciones({ refreshKey = 0 }: { refreshKey?: number }) {
  const [data, setData] = useState<Paginated | null>(null);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);

  const cargar = useCallback(async () => {
    setLoading(true);
    try {
      setData(
        await api.get<Paginated>(
          `/creditos/historial?page=${page}&page_size=${PAGE_SIZE}`,
        ),
      );
    } finally {
      setLoading(false);
    }
  }, [page]);

  useEffect(() => {
    void cargar();
  }, [cargar, refreshKey]);

  const totalPages = data ? Math.max(1, Math.ceil(data.total / PAGE_SIZE)) : 1;

  return (
    <section className="flex flex-col gap-3">
      <h2 className="text-sm font-semibold text-text">Historial de transacciones</h2>

      {loading ? (
        <div className="flex min-h-[20vh] items-center justify-center">
          <Loader2 className="animate-spin text-primary-light" size={24} />
        </div>
      ) : !data || data.items.length === 0 ? (
        <p className="rounded-lg border border-dashed border-border px-4 py-8 text-center text-sm text-text-muted">
          Aún no tienes movimientos.
        </p>
      ) : (
        <div className="overflow-hidden rounded-lg border border-border">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border bg-surface-2 text-left text-xs uppercase tracking-wide text-text-muted">
                <th className="px-4 py-2.5 font-medium">Tipo</th>
                <th className="px-4 py-2.5 font-medium">Descripción</th>
                <th className="px-4 py-2.5 text-right font-medium">Monto</th>
                <th className="px-4 py-2.5 text-right font-medium">Fecha</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((t) => {
                const credito = ES_CREDITO.has(t.tipo);
                return (
                  <tr key={t.id} className="border-b border-border last:border-0">
                    <td className="px-4 py-3 text-text">{TIPO_LABEL[t.tipo] ?? t.tipo}</td>
                    <td className="px-4 py-3 text-text-muted">{t.descripcion ?? "—"}</td>
                    <td
                      className={cn(
                        "px-4 py-3 text-right font-medium tabular-nums",
                        credito ? "text-success" : "text-text-muted",
                      )}
                    >
                      {credito ? "+" : "−"}
                      {t.monto}
                    </td>
                    <td className="px-4 py-3 text-right text-text-muted">
                      {new Date(t.created_at).toLocaleDateString("es-MX")}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {data && totalPages > 1 && (
        <div className="flex items-center justify-end gap-2 text-sm text-text-muted">
          <Button size="sm" variant="ghost" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
            Anterior
          </Button>
          <span>{page} / {totalPages}</span>
          <Button size="sm" variant="ghost" disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)}>
            Siguiente
          </Button>
        </div>
      )}
    </section>
  );
}
