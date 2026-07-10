"use client";

import { useCallback, useEffect, useRef, useState, forwardRef } from "react";
import {
  Check,
  Pencil,
  Plus,
  Trash2,
  X,
  Info,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/Button";
import type { PaqueteAdmin } from "@/hooks/usePaqueteCard";

type Props = {
  paquetes: PaqueteAdmin[];
  globalComision: number;
  onRefresh: () => void;
};

type EditableRowData = {
  mode: "create" | "edit";
  id: string | null;
  values: {
    nombre: string;
    cantidad_creditos: number;
    precio_total_usd: number;
    comision_pct: string;
    descripcion: string;
    activo: boolean;
    visible: boolean;
    destacado: boolean;
  };
};

const EMPTY_ROW: EditableRowData["values"] = {
  nombre: "",
  cantidad_creditos: 10,
  precio_total_usd: 18,
  comision_pct: "",
  descripcion: "",
  activo: true,
  visible: true,
  destacado: false,
};

function num(v: unknown): number {
  return typeof v === "string" ? Number(v) : (v as number);
}

export function PaquetesTable({ paquetes, globalComision, onRefresh }: Props) {
  const [editing, setEditing] = useState<EditableRowData | null>(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expandedDesc, setExpandedDesc] = useState<string | null>(null);
  const rowRef = useRef<HTMLTableRowElement>(null);

  // Scroll automático a la fila editable
  useEffect(() => {
    if (editing && rowRef.current) {
      rowRef.current.scrollIntoView({ behavior: "smooth", block: "center" });
    }
  }, [editing]);

  const startCreate = useCallback(() => {
    setEditing({ mode: "create", id: null, values: { ...EMPTY_ROW } });
    setError(null);
  }, []);

  const startEdit = useCallback((p: PaqueteAdmin) => {
    setEditing({
      mode: "edit",
      id: p.id,
      values: {
        nombre: p.nombre,
        cantidad_creditos: num(p.cantidad_creditos),
        precio_total_usd: num(p.precio_total_usd),
        comision_pct: p.comision_pct != null ? String(p.comision_pct) : "",
        descripcion: p.descripcion ?? "",
        activo: p.activo,
        visible: p.visible,
        destacado: p.destacado,
      },
    });
    setError(null);
  }, []);

  const cancel = useCallback(() => {
    setEditing(null);
    setError(null);
  }, []);

  const save = useCallback(async () => {
    if (!editing) return;
    setSaving(true);
    setError(null);
    try {
      const v = editing.values;
      const comision = v.comision_pct !== "" ? parseInt(v.comision_pct) : null;

      if (editing.mode === "create") {
        await api.post("/admin/paquetes", {
          nombre: v.nombre.trim(),
          cantidad_creditos: v.cantidad_creditos,
          precio_total_usd: v.precio_total_usd,
          comision_pct: comision,
          descripcion: v.descripcion.trim() || null,
          activo: v.activo,
          visible: v.visible,
          destacado: v.destacado,
        });
      } else {
        await api.patch(`/admin/paquetes/${editing.id}`, {
          nombre: v.nombre.trim(),
          cantidad_creditos: v.cantidad_creditos,
          precio_total_usd: v.precio_total_usd,
          comision_pct: comision,
          descripcion: v.descripcion.trim() || null,
          activo: v.activo,
          visible: v.visible,
          destacado: v.destacado,
        });
      }
      setEditing(null);
      onRefresh();
    } catch {
      setError(editing.mode === "create" ? "No se pudo crear el paquete." : "No se pudo guardar los cambios.");
    } finally {
      setSaving(false);
    }
  }, [editing, onRefresh]);

  const remove = useCallback(
    async (id: string) => {
      if (!confirm("¿Eliminar este paquete?")) return;
      try {
        await api.del(`/admin/paquetes/${id}`);
        onRefresh();
      } catch {
        setError("No se pudo eliminar el paquete.");
      }
    },
    [onRefresh],
  );

  const updateField = useCallback(
    <K extends keyof EditableRowData["values"]>(key: K, value: EditableRowData["values"][K]) => {
      setEditing((prev: EditableRowData | null) =>
        prev ? { ...prev, values: { ...prev.values, [key]: value } } : null,
      );
    },
    [],
  );

  return (
    <div className="rounded-xl border border-border bg-surface overflow-hidden">
      {error && (
        <div className="px-5 py-2 bg-danger/10 text-danger text-xs border-b border-border">
          {error}
        </div>
      )}

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border text-xs text-text-muted">
              <th className="text-left px-5 py-3 font-medium">Nombre</th>
              <th className="text-right px-3 py-3 font-medium w-20">Créditos</th>
              <th className="text-right px-3 py-3 font-medium w-24">
                <span className="inline-flex items-center gap-1">
                  Precio
                  <span className="group relative">
                    <Info size={12} className="text-text-muted cursor-help" />
                    <span className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1 w-48 rounded-md bg-surface-2 border border-border px-2 py-1.5 text-[11px] text-text-muted leading-tight opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-10">
                      El monto que paga el artista puede ser mayor en tarjetas
                      internacionales. El real lo determina Stripe.
                    </span>
                  </span>
                </span>
              </th>
              <th className="text-right px-3 py-3 font-medium w-20">Comisión</th>
              <th className="text-center px-3 py-3 font-medium w-20">Estado</th>
              <th className="text-right px-5 py-3 font-medium w-24">Acciones</th>
            </tr>
          </thead>
          <tbody>
            {/* Fila de creación */}
            {editing?.mode === "create" && (
              <EditableRow
                ref={rowRef}
                editing={editing}
                globalComision={globalComision}
                updateField={updateField}
                onSave={save}
                onCancel={cancel}
                saving={saving}
              />
            )}

            {/* Filas existentes */}
            {paquetes.map((p) =>
              editing?.mode === "edit" && editing.id === p.id ? (
                <EditableRow
                  key={p.id}
                  ref={rowRef}
                  editing={editing}
                  globalComision={globalComision}
                  updateField={updateField}
                  onSave={save}
                  onCancel={cancel}
                  saving={saving}
                />
              ) : (
                <tr
                  key={p.id}
                  className="border-t border-border/50 hover:bg-surface-2/50 transition-colors"
                >
                  <td className="px-5 py-3">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-text">{p.nombre}</span>
                      {p.destacado && (
                        <span className="rounded-full bg-primary/15 px-1.5 py-0.5 text-[10px] font-semibold text-primary-light">
                          ★
                        </span>
                      )}
                    </div>
                    {p.descripcion && (
                      <button
                        onClick={() =>
                          setExpandedDesc(expandedDesc === p.id ? null : p.id)
                        }
                        className="flex items-center gap-1 text-[11px] text-text-muted mt-0.5 hover:text-text transition-colors"
                      >
                        {expandedDesc === p.id ? (
                          <ChevronUp size={10} />
                        ) : (
                          <ChevronDown size={10} />
                        )}
                        Descripción
                      </button>
                    )}
                    {expandedDesc === p.id && p.descripcion && (
                      <p className="text-xs text-text-muted mt-1 pl-3">
                        {p.descripcion}
                      </p>
                    )}
                  </td>
                  <td className="text-right px-3 py-3 tabular-nums text-text">
                    {num(p.cantidad_creditos)}
                  </td>
                  <td className="text-right px-3 py-3 tabular-nums text-text">
                    ${num(p.precio_total_usd).toFixed(2)}
                  </td>
                  <td className="text-right px-3 py-3 text-text">
                    {p.comision_pct != null ? `${num(p.comision_pct)}%` : (
                      <span className="text-text-muted text-xs">Global</span>
                    )}
                  </td>
                  <td className="text-center px-3 py-3">
                    <span
                      className={cn(
                        "inline-block rounded-full px-2 py-0.5 text-[10px] font-semibold",
                        p.activo
                          ? "bg-success/15 text-success"
                          : "bg-text-muted/15 text-text-muted",
                      )}
                    >
                      {p.activo ? "Activo" : "Inactivo"}
                    </span>
                  </td>
                  <td className="text-right px-5 py-3">
                    <div className="flex items-center justify-end gap-1">
                      <button
                        onClick={() => startEdit(p)}
                        className="p-1.5 rounded-md text-text-muted hover:text-text hover:bg-surface-2 transition-colors"
                        title="Editar"
                      >
                        <Pencil size={14} />
                      </button>
                      <button
                        onClick={() => remove(p.id)}
                        className="p-1.5 rounded-md text-text-muted hover:text-danger hover:bg-danger/10 transition-colors"
                        title="Eliminar"
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </td>
                </tr>
              ),
            )}

            {/* Empty state */}
            {paquetes.length === 0 && !editing && (
              <tr>
                <td colSpan={6} className="px-5 py-10 text-center text-text-muted text-sm">
                  No hay paquetes creados. Haz clic en &ldquo;+ Nuevo paquete&rdquo; para comenzar.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Botón crear (fuera de la tabla, abajo) */}
      {!editing && (
        <div className="border-t border-border px-5 py-3">
          <button
            onClick={startCreate}
            className="flex items-center gap-1.5 text-xs text-text-muted hover:text-primary-light transition-colors"
          >
            <Plus size={14} /> Nuevo paquete
          </button>
        </div>
      )}
    </div>
  );
}

// ── Fila editable ──────────────────────────────────────────────────

const EditableRow = forwardRef<HTMLTableRowElement, {
  editing: EditableRowData;
  globalComision: number;
  updateField: <K extends keyof EditableRowData["values"]>(
    key: K,
    value: EditableRowData["values"][K],
  ) => void;
  onSave: () => void;
  onCancel: () => void;
  saving: boolean;
}>(function EditableRow(
  { editing, globalComision, updateField, onSave, onCancel, saving },
  ref,
) {
  const v = editing.values;
  const comisionDisplay = v.comision_pct !== "" ? parseInt(v.comision_pct) : globalComision;

  return (
    <tr ref={ref} className="bg-primary/5 border-t border-primary/20">
      <td className="px-5 py-2.5">
        <input
          type="text"
          value={v.nombre}
          onChange={(e) => updateField("nombre", e.target.value)}
          placeholder="Nombre del paquete"
          autoFocus
          className="w-full rounded border border-border bg-surface px-2 py-1.5 text-sm text-text focus:outline-none focus:ring-1 focus:ring-primary"
        />
        <input
          type="text"
          value={v.descripcion}
          onChange={(e) => updateField("descripcion", e.target.value)}
          placeholder="Descripción (opcional)"
          className="w-full rounded border border-border bg-surface px-2 py-1 text-xs text-text mt-1.5 focus:outline-none focus:ring-1 focus:ring-primary"
        />
      </td>
      <td className="px-3 py-2.5">
        <input
          type="number"
          min="1"
          value={v.cantidad_creditos}
          onChange={(e) => updateField("cantidad_creditos", parseInt(e.target.value) || 0)}
          className="w-full rounded border border-border bg-surface px-2 py-1.5 text-sm text-text text-right tabular-nums focus:outline-none focus:ring-1 focus:ring-primary"
        />
      </td>
      <td className="px-3 py-2.5">
        <input
          type="number"
          step="0.01"
          min="0.01"
          value={v.precio_total_usd}
          onChange={(e) => updateField("precio_total_usd", parseFloat(e.target.value) || 0)}
          className="w-full rounded border border-border bg-surface px-2 py-1.5 text-sm text-text text-right tabular-nums focus:outline-none focus:ring-1 focus:ring-primary"
        />
      </td>
      <td className="px-3 py-2.5">
        <input
          type="number"
          min="1"
          max="99"
          value={v.comision_pct}
          onChange={(e) => updateField("comision_pct", e.target.value)}
          placeholder={String(globalComision)}
          className="w-full rounded border border-border bg-surface px-2 py-1.5 text-sm text-text text-right tabular-nums placeholder:text-text-muted focus:outline-none focus:ring-1 focus:ring-primary"
        />
      </td>
      <td className="text-center px-3 py-2.5">
        <label className="inline-flex items-center gap-1.5 cursor-pointer">
          <input
            type="checkbox"
            checked={v.activo}
            onChange={(e) => updateField("activo", e.target.checked)}
            className="accent-primary"
          />
          <span className="text-xs text-text-muted">Activo</span>
        </label>
      </td>
      <td className="text-right px-5 py-2.5">
        <div className="flex items-center justify-end gap-1">
          <button
            onClick={onSave}
            disabled={saving || !v.nombre.trim() || v.cantidad_creditos <= 0 || v.precio_total_usd <= 0}
            className="p-1.5 rounded-md text-success hover:bg-success/10 transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
            title="Guardar"
          >
            <Check size={16} />
          </button>
          <button
            onClick={onCancel}
            disabled={saving}
            className="p-1.5 rounded-md text-text-muted hover:bg-surface-2 transition-colors"
            title="Cancelar"
          >
            <X size={16} />
          </button>
        </div>
      </td>
    </tr>
  );
});
