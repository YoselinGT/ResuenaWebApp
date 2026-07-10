"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";
import { api } from "@/lib/api";
import { Alert } from "@/components/ui/Alert";
import { useDashboardUser } from "@/components/layout/DashboardProvider";
import {
  ConfigAccordion,
  type ConfigCreditos,
} from "@/components/admin/ConfigAccordion";
import { PaquetesTable } from "@/components/admin/PaquetesTable";
import type { PaqueteAdmin } from "@/hooks/usePaqueteCard";

export default function AdminPaquetesPage() {
  const router = useRouter();
  const user = useDashboardUser();
  const [paquetes, setPaquetes] = useState<PaqueteAdmin[]>([]);
  const [config, setConfig] = useState<ConfigCreditos | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!user.es_admin) router.replace("/home");
  }, [user.es_admin, router]);

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const [p, c] = await Promise.all([
          api.get<PaqueteAdmin[]>("/admin/paquetes"),
          api.get<ConfigCreditos>("/admin/config/creditos"),
        ]);
        if (!active) return;
        setPaquetes(p);
        setConfig(c);
        setError(null);
      } catch {
        if (active) setError("No se pudieron cargar los paquetes.");
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => { active = false; };
  }, []);

  const refreshPaquetes = useCallback(async () => {
    try {
      const p = await api.get<PaqueteAdmin[]>("/admin/paquetes");
      setPaquetes(p);
      setError(null);
    } catch {
      setError("No se pudieron cargar los paquetes.");
    }
  }, []);

  if (loading) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center">
        <Loader2 className="animate-spin text-primary-light" size={32} />
      </div>
    );
  }

  return (
    <div className="mx-auto flex w-full max-w-[900px] flex-col gap-5 px-4">
      {/* Encabezado */}
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-text">
            Paquetes de créditos
          </h1>
          <p className="mt-1 text-sm text-text-muted">
            Define paquetes y el precio individual.
          </p>
        </div>
        <span className="rounded-full bg-primary/15 px-3 py-1 text-xs font-semibold text-primary-light">
          {paquetes.length} paquete{paquetes.length !== 1 ? "s" : ""}
        </span>
      </header>

      {error && <Alert variant="error">{error}</Alert>}

      {/* Config global — acordeón colapsado */}
      {config && (
        <ConfigAccordion config={config} onSaved={refreshPaquetes} />
      )}

      {/* Tabla de paquetes */}
      {config && (
        <PaquetesTable
          paquetes={paquetes}
          globalComision={config.comision_resuena_pct}
          onRefresh={refreshPaquetes}
        />
      )}
    </div>
  );
}
