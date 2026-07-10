"use client";

import { X } from "lucide-react";
import { Button } from "@/components/ui/Button";

type Props = {
  nombre: string;
  cantidadCreditos: number;
  precioEstimadoUsd: number;
  onConfirm: () => void;
  onCancel: () => void;
  loading: boolean;
};

export function ConfirmarCompraModal({
  nombre,
  cantidadCreditos,
  precioEstimadoUsd,
  onConfirm,
  onCancel,
  loading,
}: Props) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="mx-4 w-full max-w-md rounded-lg border border-border bg-surface p-6 shadow-lg">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-bold text-text">Confirmar compra</h2>
          <button
            onClick={onCancel}
            className="text-text-muted hover:text-text transition-colors"
          >
            <X size={18} />
          </button>
        </div>

        <div className="mb-4">
          <p className="text-sm font-medium text-text">
            {nombre} — {cantidadCreditos} créditos
          </p>
        </div>

        <div className="mb-4 rounded-md bg-surface-2 p-4">
          <p className="text-sm text-text mb-2">
            Precio estimado:{" "}
            <span className="font-semibold">
              ~${precioEstimadoUsd.toFixed(2)} USD
            </span>
          </p>

          <div className="text-xs text-text-muted space-y-1">
            <p className="font-medium text-text-secondary mb-1">
              ℹ️ El monto exacto lo determina Stripe según el tipo de tu
              tarjeta:
            </p>
            <p>· Tarjeta nacional MX: ~${precioEstimadoUsd.toFixed(2)} USD</p>
            <p>
              · Tarjeta internacional: ~$
              {(precioEstimadoUsd * 1.005).toFixed(2)} USD
            </p>
            <p>
              · Con conversión de moneda: ~$
              {(precioEstimadoUsd * 1.025).toFixed(2)} USD
            </p>
          </div>

          <p className="text-[11px] text-text-muted mt-3">
            Resuena no controla ni retiene estas diferencias — son fees
            directos de Stripe.
          </p>
        </div>

        <div className="flex items-center justify-end gap-3">
          <Button variant="ghost" size="sm" onClick={onCancel}>
            Cancelar
          </Button>
          <Button size="sm" loading={loading} onClick={onConfirm}>
            Ir a pagar →
          </Button>
        </div>
      </div>
    </div>
  );
}
