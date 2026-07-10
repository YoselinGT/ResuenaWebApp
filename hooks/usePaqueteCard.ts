"use client";

import { useCallback, useMemo, useState } from "react";
import { api } from "@/lib/api";

/** Convierte string|number a number (Python Decimal → JSON string). */
function num(v: unknown): number {
  return typeof v === "string" ? Number(v) : (v as number);
}

export type PaqueteAdmin = {
  id: string;
  nombre: string;
  cantidad_creditos: number;
  precio_total_usd: number;
  comision_pct: number | null;
  descripcion: string | null;
  activo: boolean;
  visible: boolean;
  destacado: boolean;
  transacciones_count: number;
  calculado: {
    precio_por_credito_usd: number;
    stripe_fee_estimado_usd: number;
    artista_paga_estimado_usd: number;
    curador_recibe_por_credito_usd: number;
    resuena_por_credito_usd: number;
  };
};

type Values = {
  nombre: string;
  descripcion: string;
  precio_total_usd: number;
  comision_pct: number | null;
  activo: boolean;
  visible: boolean;
  destacado: boolean;
};

export function usePaqueteCard(paquete: PaqueteAdmin, globalComision: number) {
  const [values, setValues] = useState<Values>({
    nombre: paquete.nombre,
    descripcion: paquete.descripcion ?? "",
    precio_total_usd: num(paquete.precio_total_usd),
    comision_pct: paquete.comision_pct != null ? num(paquete.comision_pct) : null,
    activo: paquete.activo,
    visible: paquete.visible,
    destacado: paquete.destacado,
  });
  const [saving, setSaving] = useState(false);

  const isDirty = useMemo(
    () =>
      values.nombre !== paquete.nombre ||
      values.descripcion !== (paquete.descripcion ?? "") ||
      values.precio_total_usd !== num(paquete.precio_total_usd) ||
      values.comision_pct !== (paquete.comision_pct != null ? num(paquete.comision_pct) : null) ||
      values.visible !== paquete.visible ||
      values.destacado !== paquete.destacado,
    [values, paquete],
  );

  const comisionEfectiva = values.comision_pct ?? globalComision;
  const precioUsd = num(values.precio_total_usd);
  const cantidad = num(paquete.cantidad_creditos);
  const ppc = precioUsd / cantidad;
  const stripeFee = precioUsd * 0.036 + 0.17;
  const artistaPaga = precioUsd + stripeFee;
  const curadorPorCredito = ppc * (1 - comisionEfectiva / 100);
  const resuenaPorCredito = ppc * (comisionEfectiva / 100);

  const toggleActivo = useCallback(async () => {
    const nuevoActivo = !values.activo;
    setValues((v) => ({ ...v, activo: nuevoActivo }));
    try {
      await api.patch(`/admin/paquetes/${paquete.id}`, {
        activo: nuevoActivo,
      });
    } catch {
      setValues((v) => ({ ...v, activo: !nuevoActivo }));
    }
  }, [values.activo, paquete.id]);

  const save = useCallback(async () => {
    setSaving(true);
    try {
      await api.patch(`/admin/paquetes/${paquete.id}`, {
        nombre: values.nombre,
        descripcion: values.descripcion || null,
        precio_total_usd: values.precio_total_usd,
        comision_pct: values.comision_pct,
        visible: values.visible,
        destacado: values.destacado,
      });
    } finally {
      setSaving(false);
    }
  }, [values, paquete.id]);

  const updateField = useCallback(
    <K extends keyof Values>(key: K, value: Values[K]) => {
      setValues((v) => ({ ...v, [key]: value }));
    },
    [],
  );

  return {
    values,
    isDirty,
    saving,
    comisionEfectiva,
    ppc,
    stripeFee,
    artistaPaga,
    curadorPorCredito,
    resuenaPorCredito,
    toggleActivo,
    save,
    updateField,
  };
}
