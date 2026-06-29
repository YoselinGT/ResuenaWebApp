/**
 * Layout del grupo de rutas sin sesión (auth).
 * Aplica el shell con gradiente radial morado y centra el contenido.
 */
export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <main className="auth-shell flex min-h-screen flex-col items-center justify-center px-4 py-12">
      {children}
    </main>
  );
}
