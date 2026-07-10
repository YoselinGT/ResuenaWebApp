"use client";

import { useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { AnimatePresence, motion } from "framer-motion";
import {
  Building2,
  ClipboardCheck,
  Coins,
  CreditCard,
  Home,
  Inbox,
  LayoutDashboard,
  ListMusic,
  Megaphone,
  UserCircle,
  Wallet,
  X,
  type LucideIcon,
} from "lucide-react";
import { create } from "zustand";
import { Logo } from "@/components/ui/Logo";
import { cn } from "@/lib/utils";
import {
  useDashboardUser,
  type TipoUsuario,
} from "@/components/layout/DashboardProvider";

/** Store del estado abierto/cerrado del sidebar en móvil. Lo comparte el Header. */
type SidebarState = {
  open: boolean;
  setOpen: (open: boolean) => void;
  toggle: () => void;
};

export const useSidebar = create<SidebarState>((set) => ({
  open: false,
  setOpen: (open) => set({ open }),
  toggle: () => set((s) => ({ open: !s.open })),
}));

type NavItem = { label: string; href: string; Icon: LucideIcon };

// Menú estático por tipo de usuario (dinámico en fases futuras). Varias rutas
// se construyen en fases posteriores; aquí solo definen la navegación prevista.
const NAV: Record<TipoUsuario, NavItem[]> = {
  artista: [
    { label: "Inicio", href: "/home", Icon: Home },
    { label: "Mis campañas", href: "/campanas", Icon: Megaphone },
    { label: "Créditos", href: "/artista/creditos", Icon: Coins },
    { label: "Mi sello", href: "/artista/sello", Icon: Building2 },
    { label: "Mi perfil", href: "/mi-perfil", Icon: UserCircle },
  ],
  curador: [
    { label: "Inicio", href: "/home", Icon: Home },
    { label: "Campañas disponibles", href: "/campanas", Icon: Megaphone },
    { label: "Mis medios", href: "/curador/medios", Icon: ListMusic },
    { label: "Mis entregas", href: "/entregas", Icon: Inbox },
    { label: "Balance", href: "/balance", Icon: Wallet },
    { label: "Mi perfil", href: "/mi-perfil", Icon: UserCircle },
  ],
  admin: [
    { label: "Inicio", href: "/home", Icon: Home },
    { label: "Solicitudes", href: "/admin/solicitudes", Icon: ClipboardCheck },
    { label: "Usuarios", href: "/admin/usuarios", Icon: LayoutDashboard },
    { label: "Paquetes", href: "/admin/paquetes", Icon: CreditCard },
    { label: "Mi perfil", href: "/mi-perfil", Icon: UserCircle },
  ],
};

function isActive(pathname: string, href: string): boolean {
  return href === "/home" ? pathname === href : pathname.startsWith(href);
}

function NavLinks({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();
  const { tipo, es_admin } = useDashboardUser();
  const items = es_admin ? NAV.admin : (NAV[tipo] ?? NAV.artista);

  return (
    <nav className="flex flex-col gap-1" aria-label="Navegación principal">
      {items.map(({ label, href, Icon }) => {
        const active = isActive(pathname, href);
        return (
          <Link
            key={href}
            href={href}
            onClick={onNavigate}
            aria-current={active ? "page" : undefined}
            className={cn(
              "flex items-center gap-3 rounded-md px-3 py-2.5 text-sm font-medium transition-colors",
              active
                ? "bg-primary/15 text-text shadow-glow"
                : "text-text-muted hover:bg-surface-2 hover:text-text",
            )}
          >
            <Icon
              size={18}
              className={cn("shrink-0", active && "text-primary-light")}
            />
            {label}
          </Link>
        );
      })}
    </nav>
  );
}

export function Sidebar() {
  const { open, setOpen } = useSidebar();
  const pathname = usePathname();

  // Cierra el overlay móvil al navegar.
  useEffect(() => {
    setOpen(false);
  }, [pathname, setOpen]);

  // Cierra con Escape y bloquea el scroll del fondo cuando está abierto.
  useEffect(() => {
    if (!open) return;
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") setOpen(false);
    }
    document.addEventListener("keydown", onKey);
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = "";
    };
  }, [open, setOpen]);

  return (
    <>
      {/* Desktop: rail fijo */}
      <aside className="hidden w-64 shrink-0 border-r border-border bg-surface md:flex md:flex-col">
        <div className="flex h-16 items-center px-5">
          <Logo width={140} href="/home" />
        </div>
        <div className="flex-1 overflow-y-auto px-3 py-4">
          <NavLinks />
        </div>
      </aside>

      {/* Móvil: overlay deslizable */}
      <AnimatePresence>
        {open && (
          <motion.div
            className="fixed inset-0 z-50 md:hidden"
            initial="closed"
            animate="open"
            exit="closed"
          >
            <motion.div
              className="absolute inset-0 bg-base/80 backdrop-blur-sm"
              variants={{ open: { opacity: 1 }, closed: { opacity: 0 } }}
              transition={{ duration: 0.2 }}
              onClick={() => setOpen(false)}
              aria-hidden
            />
            <motion.aside
              className="absolute left-0 top-0 flex h-full w-72 max-w-[80%] flex-col border-r border-border bg-surface"
              role="dialog"
              aria-modal="true"
              aria-label="Menú"
              variants={{
                open: { x: 0 },
                closed: { x: "-100%" },
              }}
              transition={{ type: "tween", ease: [0.25, 0.46, 0.45, 0.94], duration: 0.28 }}
            >
              <div className="flex h-16 items-center justify-between px-5">
                <Logo width={130} href="/home" />
                <button
                  type="button"
                  onClick={() => setOpen(false)}
                  aria-label="Cerrar menú"
                  className="text-text-muted transition-colors hover:text-text"
                >
                  <X size={22} />
                </button>
              </div>
              <div className="flex-1 overflow-y-auto px-3 py-4">
                <NavLinks onNavigate={() => setOpen(false)} />
              </div>
            </motion.aside>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
