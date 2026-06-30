"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Loader2 } from "lucide-react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/Button";

type Balance = { saldo_creditos: number };

export default function CreditosSuccessPage() {
  const [saldo, setSaldo] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // El webhook acredita de forma asíncrona; reintenta un par de veces.
    let intentos = 0;
    let cancelado = false;

    async function revalidar() {
      try {
        const b = await api.get<Balance>("/creditos/balance");
        if (!cancelado) setSaldo(b.saldo_creditos);
      } catch {
        /* ignora */
      } finally {
        intentos += 1;
        if (!cancelado && intentos < 3) {
          setTimeout(revalidar, 2000);
        } else if (!cancelado) {
          setLoading(false);
        }
      }
    }
    void revalidar();
    return () => {
      cancelado = true;
    };
  }, []);

  return (
    <div className="mx-auto mt-8 w-full max-w-md rounded-lg border border-border bg-surface p-8 text-center shadow-glow">
      <div
        className="auth-success-check mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-success/15 text-3xl text-success"
        aria-hidden
      >
        ✓
      </div>
      <h1 className="text-xl font-bold text-text">¡Pago completado!</h1>
      <p className="mt-2 text-sm text-text-muted">
        Estamos acreditando tus créditos. Tu saldo se actualizará en unos segundos.
      </p>
      <div className="mt-4 flex items-center justify-center gap-2 text-sm text-text-muted">
        <span>Saldo actual:</span>
        {loading ? (
          <Loader2 className="animate-spin text-primary-light" size={16} />
        ) : (
          <span className="font-bold text-text">{saldo ?? "—"}</span>
        )}
      </div>
      <Link href="/artista/creditos" className="mt-6 inline-block">
        <Button>Volver a créditos</Button>
      </Link>
    </div>
  );
}
