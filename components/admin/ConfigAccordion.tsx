"use client";

import { useCallback, useEffect, useState } from "react";
import { ChevronDown, ChevronUp, Settings, Save } from "lucide-react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Alert } from "@/components/ui/Alert";

export type ConfigCreditos = {
  precio_credito_individual_usd: number;
  comision_resuena_pct: number;
  stripe_pct_nacional: number;
  stripe_fixed_usd: number;
  stripe_pct_internacional: number;
  stripe_pct_conversion_moneda: number;
  stripe_pct_oxxo: number;
  stripe_fixed_disputa_usd: number;
  stripe_escenario_default: string;
};

type Props = {
  config: ConfigCreditos;
  onSaved: () => void;
};

function num(v: unknown): number {
  return typeof v === "string" ? Number(v) : (v as number);
}

const ESCENARIOS = [
  { value: "nacional", label: "Nacional" },
  { value: "internacional", label: "Internacional" },
  { value: "oxxo", label: "OXXO" },
] as const;

export function ConfigAccordion({ config, onSaved }: Props) {
  const [values, setValues] = useState(config);
  const [expanded, setExpanded] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  useEffect(() => setValues(config), [config]);

  const update = useCallback(
    <K extends keyof ConfigCreditos>(key: K, value: ConfigCreditos[K]) => {
      setValues((v) => ({ ...v, [key]: value }));
      setSuccess(false);
    },
    [],
  );

  const precioCredito = num(values.precio_credito_individual_usd);

  async function handleSave() {
    setSaving(true);
    setError(null);
    setSuccess(false);
    try {
      await api.patch("/admin/config/creditos", {
        precio_credito_individual_usd: values.precio_credito_individual_usd,
        comision_resuena_pct: values.comision_resuena_pct,
        stripe_pct_nacional: values.stripe_pct_nacional,
        stripe_fixed_usd: values.stripe_fixed_usd,
        stripe_pct_internacional: values.stripe_pct_internacional,
        stripe_pct_conversion_moneda: values.stripe_pct_conversion_moneda,
        stripe_pct_oxxo: values.stripe_pct_oxxo,
        stripe_escenario_default: values.stripe_escenario_default,
      });
      setSuccess(true);
      onSaved();
    } catch {
      setError("No se pudo guardar la configuración.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="rounded-xl border border-border bg-surface overflow-hidden">
      {/* Fila resumen — siempre visible */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex w-full items-center gap-3 px-5 py-3.5 text-left hover:bg-surface-2 transition-colors"
      >
        <Settings size={16} className="text-text-muted shrink-0" />
        <span className="text-sm font-medium text-text">Configuración global</span>
        <span className="text-xs text-text-muted ml-1">
          ${precioCredito.toFixed(2)}/crédito · {values.comision_resuena_pct}% comisión
        </span>
        <span className="ml-auto text-text-muted">
          {expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        </span>
      </button>

      {/* Panel expandido */}
      {expanded && (
        <div className="border-t border-border px-5 py-4 space-y-4">
          {error ? <Alert variant="error">{error}</Alert> : null}
          {success ? <Alert variant="success">Configuración guardada.</Alert> : null}

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label className="block text-xs text-text-muted mb-1">
                Precio crédito individual (USD)
              </label>
              <input
                type="number"
                step="0.01"
                min="0.01"
                value={values.precio_credito_individual_usd}
                onChange={(e) =>
                  update("precio_credito_individual_usd", parseFloat(e.target.value) || 0)
                }
                className="w-full rounded-md border border-border bg-surface-2 px-3 py-2 text-sm text-text focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>
            <div>
              <label className="block text-xs text-text-muted mb-1">
                Comisión Resuena %
              </label>
              <input
                type="number"
                min="1"
                max="99"
                value={values.comision_resuena_pct}
                onChange={(e) =>
                  update("comision_resuena_pct", parseInt(e.target.value) || 50)
                }
                className="w-full rounded-md border border-border bg-surface-2 px-3 py-2 text-sm text-text focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>
          </div>

          {/* Stripe fees — sub-acordeón */}
          <StripeFeesSection values={values} update={update} />

          <div className="flex items-center justify-between pt-2">
            <p className="text-[11px] text-text-muted max-w-md">
              Los fees de Stripe son tarifas publicadas. Actualizarlos aquí no
              afecta lo que Stripe realmente cobra.
            </p>
            <Button size="sm" loading={saving} onClick={handleSave}>
              <Save size={14} /> Guardar
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}

function StripeFeesSection({
  values,
  update,
}: {
  values: ConfigCreditos;
  update: <K extends keyof ConfigCreditos>(key: K, value: ConfigCreditos[K]) => void;
}) {
  const [open, setOpen] = useState(false);

  return (
    <div>
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 text-xs text-text-muted hover:text-text transition-colors"
      >
        {open ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
        Comisiones de Stripe
      </button>

      {open && (
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 mt-3 pl-4 border-l-2 border-border">
          <Field
            label="Fee % tarjeta nacional"
            step="0.001"
            value={values.stripe_pct_nacional}
            onChange={(v) => update("stripe_pct_nacional", v)}
          />
          <Field
            label="Fee fijo por transacción (USD)"
            step="0.01"
            value={values.stripe_fixed_usd}
            onChange={(v) => update("stripe_fixed_usd", v)}
          />
          <Field
            label="Fee adicional % internacional"
            step="0.001"
            value={values.stripe_pct_internacional}
            onChange={(v) => update("stripe_pct_internacional", v)}
          />
          <Field
            label="Fee adicional % conversión moneda"
            step="0.001"
            value={values.stripe_pct_conversion_moneda}
            onChange={(v) => update("stripe_pct_conversion_moneda", v)}
          />
          <Field
            label="Fee % OXXO"
            step="0.001"
            value={values.stripe_pct_oxxo}
            onChange={(v) => update("stripe_pct_oxxo", v)}
          />
          <div>
            <label className="block text-xs text-text-muted mb-1">
              Escenario default
            </label>
            <select
              value={values.stripe_escenario_default}
              onChange={(e) =>
                update(
                  "stripe_escenario_default",
                  e.target.value as ConfigCreditos["stripe_escenario_default"],
                )
              }
              className="w-full rounded-md border border-border bg-surface-2 px-3 py-2 text-sm text-text focus:outline-none focus:ring-2 focus:ring-primary"
            >
              {ESCENARIOS.map((e) => (
                <option key={e.value} value={e.value}>
                  {e.label}
                </option>
              ))}
            </select>
          </div>
        </div>
      )}
    </div>
  );
}

function Field({
  label,
  step,
  value,
  onChange,
}: {
  label: string;
  step: string;
  value: number;
  onChange: (v: number) => void;
}) {
  return (
    <div>
      <label className="block text-xs text-text-muted mb-1">{label}</label>
      <input
        type="number"
        step={step}
        min="0"
        value={value}
        onChange={(e) => onChange(parseFloat(e.target.value) || 0)}
        className="w-full rounded-md border border-border bg-surface-2 px-3 py-2 text-sm text-text focus:outline-none focus:ring-2 focus:ring-primary"
      />
    </div>
  );
}
