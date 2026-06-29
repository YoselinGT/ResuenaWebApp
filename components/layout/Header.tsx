"use client";

import { Menu } from "lucide-react";
import { Logo } from "@/components/ui/Logo";
import { UserMenu } from "@/components/layout/UserMenu";
import { useSidebar } from "@/components/layout/Sidebar";

/**
 * Barra superior del dashboard: en móvil muestra el botón hamburguesa (abre el
 * Sidebar) + logo; el menú de usuario (Mi Perfil / Salir) está siempre a la
 * derecha.
 */
export function Header() {
  const toggle = useSidebar((s) => s.toggle);

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center justify-between gap-3 border-b border-border bg-surface/80 px-4 backdrop-blur sm:px-6">
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={toggle}
          aria-label="Abrir menú"
          className="rounded-md p-1.5 text-text-muted transition-colors hover:bg-surface-2 hover:text-text md:hidden"
        >
          <Menu size={22} />
        </button>
        <Logo width={120} href="/home" className="md:hidden" />
      </div>

      <UserMenu />
    </header>
  );
}
