"use client";

import { Coins } from "lucide-react";
import { Button } from "@/components/ui/Button";

export type Paquete = {
  id: string;
  nombre: string;
  cantidad_creditos: number;
  precio_total_usd: number;
  descripcion: string | null;
  destacado: boolean;
  calculado: {
    precio_por_credito_usd: number;
    stripe_fee_estimado_usd: number;
    artista_paga_estimado_usd: number;
    curador_recibe_por_credito_usd: number;
    resuena_por_credito_usd: number;
  };
};

type Props = {
  paquete: Paquete;
  onBuy: () => void;
  buying: boolean;
};

export function PaqueteCard({ paquete, onBuy, buying }: Props) {
  return (
    <article
      className={`flex flex-col items-center gap-3 rounded-lg border bg-surface p-6 text-center ${
        paquete.destacado
          ? "border-accent-purple shadow-glow"
          : "border-border"
      }`}
    >
      {paquete.destacado && (
        <span className="rounded-full bg-primary/15 px-2 py-0.5 text-[10px] font-semibold text-primary-light">
          ★ Más popular
        </span>
      )}
      <span className="flex h-12 w-12 items-center justify-center rounded-full bg-primary/15 text-primary-light">
        <Coins size={22} />
      </span>
      <p className="text-xs font-medium text-text">{paquete.nombre}</p>
      <p className="text-3xl font-bold text-text tabular-nums">
        {paquete.cantidad_creditos}
      </p>
      <p className="text-sm text-text-muted">créditos</p>
      <p className="text-lg font-semibold text-text">
        ~${Number(paquete.calculado.artista_paga_estimado_usd).toFixed(2)}{" "}
        <span className="text-xs text-text-muted font-normal">USD est.</span>
      </p>
      <p className="text-[11px] text-text-muted">
        El monto final lo determina Stripe al momento del pago
      </p>
      <Button fullWidth loading={buying} onClick={onBuy}>
        Comprar
      </Button>
    </article>
  );
}
