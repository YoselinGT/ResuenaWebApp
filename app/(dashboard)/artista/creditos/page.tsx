"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Coins, Loader2 } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import { Alert } from "@/components/ui/Alert";
import { useDashboardUser } from "@/components/layout/DashboardProvider";
import { PaqueteCard, type Paquete } from "@/components/creditos/PaqueteCard";
import { HistorialTransacciones } from "@/components/creditos/HistorialTransacciones";

type Balance = { saldo_creditos: number; saldo_pendiente_retiro: number };

export default function CreditosPage() {
  const router = useRouter();
  const user = useDashboardUser();
  const [balance, setBalance] = useState<Balance | null>(null);
  const [paquetes, setPaquetes] = useState<Paquete[]>([]);
  const [loading, setLoading] = useState(true);
  const [comprando, setComprando] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

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

  async function comprar(cantidad: number) {
    setComprando(cantidad);
    setError(null);
    try {
      const { checkout_url } = await api.post<{ checkout_url: string }>(
        "/creditos/checkout",
        { cantidad_creditos: cantidad },
      );
      window.location.href = checkout_url; // redirige a Stripe Checkout
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo iniciar el pago.");
      setComprando(null);
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
              key={p.cantidad}
              paquete={p}
              onBuy={comprar}
              buying={comprando === p.cantidad}
            />
          ))}
        </div>
      </section>

      <HistorialTransacciones />
    </div>
  );
}
