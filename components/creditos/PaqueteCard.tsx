"use client";

import { Coins } from "lucide-react";
import { Button } from "@/components/ui/Button";

export type Paquete = {
  cantidad: number;
  precio_unitario_mxn: number;
  precio_total_mxn: number;
};

type Props = {
  paquete: Paquete;
  onBuy: (cantidad: number) => void;
  buying: boolean;
};

export function PaqueteCard({ paquete, onBuy, buying }: Props) {
  return (
    <article className="flex flex-col items-center gap-3 rounded-lg border border-border bg-surface p-6 text-center shadow-glow">
      <span className="flex h-12 w-12 items-center justify-center rounded-full bg-primary/15 text-primary-light">
        <Coins size={22} />
      </span>
      <p className="text-3xl font-bold text-text tabular-nums">{paquete.cantidad}</p>
      <p className="text-sm text-text-muted">créditos</p>
      <p className="text-lg font-semibold text-text">
        ${paquete.precio_total_mxn.toLocaleString("es-MX")} MXN
      </p>
      <Button fullWidth loading={buying} onClick={() => onBuy(paquete.cantidad)}>
        Comprar
      </Button>
    </article>
  );
}
