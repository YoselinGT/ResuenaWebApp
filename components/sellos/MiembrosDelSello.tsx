"use client";

import { useState } from "react";
import { Crown, Trash2 } from "lucide-react";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";
import { Avatar } from "@/components/ui/Avatar";
import { Button } from "@/components/ui/Button";
import { useDashboardUser } from "@/components/layout/DashboardProvider";

export type Miembro = {
  id: string;
  nombre_completo: string;
  correo: string;
  rol: string;
  activo: boolean;
  foto_url: string | null;
};

const ROL_BADGE: Record<string, { label: string; cls: string }> = {
  owner: { label: "Owner", cls: "bg-primary/20 text-primary-light" },
  manager: { label: "Manager", cls: "bg-sky-500/20 text-sky-300" },
  artista: { label: "Artista", cls: "bg-white/10 text-text-muted" },
};

type Props = {
  selloId: string;
  miembros: Miembro[];
  miRol: string;
  onChanged: () => void;
};

export function MiembrosDelSello({ selloId, miembros, miRol, onChanged }: Props) {
  const me = useDashboardUser();
  const [busyId, setBusyId] = useState<string | null>(null);

  const soyOwner = miRol === "owner";

  async function eliminar(artistaId: string) {
    setBusyId(artistaId);
    try {
      await api.del(`/sellos/${selloId}/miembros/${artistaId}`);
      onChanged();
    } finally {
      setBusyId(null);
    }
  }

  async function hacerOwner(artistaId: string) {
    setBusyId(artistaId);
    try {
      await api.post(`/sellos/${selloId}/transferir-ownership`, {
        nuevo_owner_id: artistaId,
      });
      onChanged();
    } finally {
      setBusyId(null);
    }
  }

  return (
    <div className="overflow-hidden rounded-lg border border-border">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-border bg-surface-2 text-left text-xs uppercase tracking-wide text-text-muted">
            <th className="px-4 py-2.5 font-medium">Miembro</th>
            <th className="px-4 py-2.5 font-medium">Rol</th>
            {soyOwner && <th className="px-4 py-2.5 text-right font-medium">Acciones</th>}
          </tr>
        </thead>
        <tbody>
          {miembros.map((m) => {
            const badge = ROL_BADGE[m.rol] ?? ROL_BADGE.artista;
            const esYo = m.id === me.id;
            const puedeActuar = soyOwner && !esYo && m.activo;
            return (
              <tr key={m.id} className="border-b border-border last:border-0">
                <td className="px-4 py-3">
                  <div className="flex items-center gap-3">
                    <Avatar name={m.nombre_completo} src={m.foto_url} size={36} />
                    <div className="min-w-0">
                      <p className="truncate font-medium text-text">
                        {m.nombre_completo}
                        {esYo && (
                          <span className="ml-1.5 text-xs text-text-muted">(tú)</span>
                        )}
                      </p>
                      <p className="truncate text-xs text-text-muted">{m.correo}</p>
                    </div>
                  </div>
                </td>
                <td className="px-4 py-3">
                  <span
                    className={cn(
                      "inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium",
                      badge.cls,
                    )}
                  >
                    {badge.label}
                  </span>
                  {!m.activo && (
                    <span className="ml-2 text-xs text-text-muted">inactivo</span>
                  )}
                </td>
                {soyOwner && (
                  <td className="px-4 py-3">
                    <div className="flex justify-end gap-1">
                      {puedeActuar && (
                        <>
                          <Button
                            variant="ghost"
                            size="sm"
                            loading={busyId === m.id}
                            onClick={() => hacerOwner(m.id)}
                            aria-label={`Transferir ownership a ${m.nombre_completo}`}
                            title="Hacer owner"
                          >
                            <Crown size={15} />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            loading={busyId === m.id}
                            onClick={() => eliminar(m.id)}
                            aria-label={`Eliminar a ${m.nombre_completo}`}
                            title="Eliminar del sello"
                          >
                            <Trash2 size={15} />
                          </Button>
                        </>
                      )}
                    </div>
                  </td>
                )}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
