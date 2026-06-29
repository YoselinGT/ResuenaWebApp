"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ChevronDown, LogOut, UserCircle } from "lucide-react";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";
import { Avatar } from "@/components/ui/Avatar";
import {
  useDashboardUser,
  type TipoUsuario,
} from "@/components/layout/DashboardProvider";

const TIPO_LABEL: Record<TipoUsuario, string> = {
  artista: "Artista",
  curador: "Curador",
  admin: "Administrador",
};

export function UserMenu() {
  const router = useRouter();
  const user = useDashboardUser();
  const [open, setOpen] = useState(false);
  const [loggingOut, setLoggingOut] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    function onClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") setOpen(false);
    }
    document.addEventListener("mousedown", onClick);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onClick);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  async function logout() {
    setLoggingOut(true);
    try {
      await api.post("/auth/logout");
    } catch {
      // Aun ante error limpiamos la sesión del lado del cliente.
    }
    router.push("/login");
    router.refresh();
  }

  return (
    <div className="relative" ref={ref}>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-haspopup="menu"
        aria-expanded={open}
        className={cn(
          "flex items-center gap-2 rounded-full py-1 pl-1 pr-2 transition-colors",
          "hover:bg-surface-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary",
        )}
      >
        <Avatar name={user.nombre_completo} size={34} />
        <span className="hidden max-w-[10rem] truncate text-sm font-medium text-text sm:block">
          {user.nombre_completo}
        </span>
        <ChevronDown
          size={16}
          className={cn(
            "text-text-muted transition-transform",
            open && "rotate-180",
          )}
        />
      </button>

      {open && (
        <div
          role="menu"
          className="absolute right-0 z-40 mt-2 w-60 overflow-hidden rounded-lg border border-border bg-surface shadow-glow-lg"
        >
          <div className="border-b border-border px-4 py-3">
            <p className="truncate text-sm font-semibold text-text">
              {user.nombre_completo}
            </p>
            <p className="truncate text-xs text-text-muted">{user.correo}</p>
            <span className="mt-1.5 inline-block rounded-full bg-primary/15 px-2 py-0.5 text-xs text-primary-light">
              {TIPO_LABEL[user.tipo]}
            </span>
          </div>

          <div className="p-1.5">
            <Link
              href="/mi-perfil"
              role="menuitem"
              onClick={() => setOpen(false)}
              className="flex items-center gap-2.5 rounded-md px-3 py-2 text-sm text-text-muted transition-colors hover:bg-surface-2 hover:text-text"
            >
              <UserCircle size={17} />
              Mi perfil
            </Link>
            <button
              type="button"
              role="menuitem"
              onClick={logout}
              disabled={loggingOut}
              className="flex w-full items-center gap-2.5 rounded-md px-3 py-2 text-sm text-danger transition-colors hover:bg-danger/10 disabled:opacity-60"
            >
              <LogOut size={17} />
              {loggingOut ? "Saliendo…" : "Salir"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
