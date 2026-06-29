"use client";

import { createContext, useContext, type ReactNode } from "react";

export type TipoUsuario = "artista" | "curador" | "admin";

export type DashboardUser = {
  id: string;
  nombre_completo: string;
  correo: string;
  tipo: TipoUsuario;
};

const DashboardUserContext = createContext<DashboardUser | null>(null);

/**
 * Provee al árbol cliente los datos del usuario en sesión, obtenidos en el
 * Server Component `(dashboard)/layout.tsx`. No hace fetch: solo distribuye.
 */
export function DashboardProvider({
  user,
  children,
}: {
  user: DashboardUser;
  children: ReactNode;
}) {
  return (
    <DashboardUserContext.Provider value={user}>
      {children}
    </DashboardUserContext.Provider>
  );
}

/** Hook para leer el usuario en sesión dentro del dashboard. */
export function useDashboardUser(): DashboardUser {
  const user = useContext(DashboardUserContext);
  if (!user) {
    throw new Error(
      "useDashboardUser debe usarse dentro de <DashboardProvider>",
    );
  }
  return user;
}
