"use client";

import { useEffect, useState } from "react";
import { Coins, Loader2 } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import { Alert } from "@/components/ui/Alert";
import { useDashboardUser } from "@/components/layout/DashboardProvider";
import { PaqueteCard, type Paquete } from "@/components/creditos/PaqueteCard";
import { ConfirmarCompraModal } from "@/components/creditos/ConfirmarCompraModal";
import { HistorialTransacciones } from "@/components/creditos/HistorialTransacciones";

type Balance = { saldo_creditos: number; saldo_pendiente_retiro: number };

export default function CreditosPage() {
  const router = useRouter();
  const user = useDashboardUser();
  const [balance, setBalance] = useState<Balance | null>(null);
  const [paquetes, setPaquetes] = useState<Paquete[]>([]);
  const [loading, setLoading] = useState(true);
  const [comprando, setComprando] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [modal, setModal] = useState<{
    paqueteId: string;
    nombre: string;
    cantidad: number;
    precioEstimado: number;
  } | null>(null);
  const [modalLoading, setModalLoading] = useState(false);

  // Compra individual
  const [individualQty, setIndividualQty] = useState<number>(1);
  const [individualPrice, setIndividualPrice] = useState<number>(2.0);

  useEffect(() => {
    if (user.tipo !== "artista") router.replace("/home");
  }, [user.tipo, router]);

  useEffect(() => {
    Promise.all([
      api.get<Balance>("/creditos/balance"),
      api.get<Paquete[]>("/creditos/paquetes"),
    ])
      .then(([b, p]) => {
        setBalance(b);
        setPaquetes(p);
      })
      .catch(() => setError("No se pudieron cargar tus créditos."))
      .finally(() => setLoading(false));
  }, []);

  function abrirModal(paqueteId: string, nombre: string, cantidad: number, precioUsd: number) {
    const stripeFee = precioUsd * 0.036 + 0.17;
    setModal({
      paqueteId,
      nombre,
      cantidad,
      precioEstimado: precioUsd + stripeFee,
    });
  }

  function abrirModalIndividual() {
    const precioNeto = individualPrice * individualQty;
    const stripeFee = precioNeto * 0.036 + 0.17;
    setModal({
      paqueteId: "",
      nombre: "Créditos sueltos",
      cantidad: individualQty,
      precioEstimado: precioNeto + stripeFee,
    });
  }

  async function confirmarCompra() {
    if (!modal) return;
    setModalLoading(true);
    setError(null);
    try {
      const body = modal.paqueteId
        ? { paquete_id: modal.paqueteId }
        : { cantidad_creditos: modal.cantidad };
      const { checkout_url } = await api.post<{ checkout_url: string }>(
        "/creditos/checkout",
        body,
      );
      window.location.href = checkout_url;
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo iniciar el pago.");
      setModalLoading(false);
      setModal(null);
    }
  }

  if (loading) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center">
        <Loader2 className="animate-spin text-primary-light" size={32} />
      </div>
    );
  }

  return (
    <div className="mx-auto flex w-full max-w-5xl flex-col gap-8">
      <header>
        <h1 className="text-2xl font-bold tracking-tight text-text">Créditos</h1>
        <p className="mt-1 text-sm text-text-muted">
          Compra créditos para lanzar campañas a curadores.
        </p>
      </header>

      {error && <Alert variant="error">{error}</Alert>}

      <section className="flex items-center gap-4 rounded-lg border border-border bg-surface p-6 shadow-glow">
        <span className="flex h-14 w-14 items-center justify-center rounded-full bg-primary/15 text-primary-light">
          <Coins size={26} />
        </span>
        <div>
          <p className="text-sm text-text-muted">Saldo disponible</p>
          <p className="text-4xl font-bold text-text tabular-nums">
            {balance?.saldo_creditos ?? 0}
          </p>
        </div>
      </section>

      <section className="flex flex-col gap-3">
        <h2 className="text-sm font-semibold text-text">Comprar créditos</h2>
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          {paquetes.map((p) => (
            <PaqueteCard
              key={p.id}
              paquete={p}
              onBuy={() =>
                abrirModal(p.id, p.nombre, Number(p.cantidad_creditos), Number(p.precio_total_usd))
              }
              buying={comprando === p.id}
            />
          ))}
        </div>
      </section>

      {/* Transparencia */}
      {paquetes.length > 0 && (
        <p className="text-xs text-text-muted">
          De cada crédito: $
          {(Number(paquetes[0]?.precio_total_usd) / Number(paquetes[0]?.cantidad_creditos) * 0.5).toFixed(2)}{" "}
          USD al curador · $
          {(Number(paquetes[0]?.precio_total_usd) / Number(paquetes[0]?.cantidad_creditos) * 0.5).toFixed(2)}{" "}
          USD a Resuena
        </p>
      )}

      {/* Compra individual */}
      <section className="rounded-lg border border-border bg-surface p-5">
        <p className="text-sm text-text-muted mb-3">
          ¿Prefieres comprar créditos sueltos? $2.00 USD/crédito
        </p>
        <div className="flex items-center gap-3">
          <input
            type="number"
            min="1"
            value={individualQty}
            onChange={(e) => setIndividualQty(parseInt(e.target.value) || 1)}
            className="w-20 rounded-md border border-border bg-surface-2 px-3 py-2 text-sm text-text focus:outline-none focus:ring-2 focus:ring-primary"
          />
          <button
            onClick={abrirModalIndividual}
            className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-text hover:bg-primary-light transition-colors"
          >
            Comprar {individualQty} créditos
          </button>
        </div>
      </section>

      <HistorialTransacciones />

      {modal && (
        <ConfirmarCompraModal
          nombre={modal.nombre}
          cantidadCreditos={modal.cantidad}
          precioEstimadoUsd={modal.precioEstimado}
          onConfirm={confirmarCompra}
          onCancel={() => setModal(null)}
          loading={modalLoading}
        />
      )}
    </div>
  );
}
