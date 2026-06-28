export default function HomePage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-4 p-8 text-center">
      <h1 className="text-5xl font-bold tracking-tight text-primary">Resuena</h1>
      <p className="max-w-md text-lg text-text-muted">
        Plataforma de gestión de campañas musicales. Conecta artistas con
        profesionales de la industria.
      </p>
      <span className="rounded-full border border-border bg-surface-2 px-4 py-1.5 text-sm text-text-muted">
        Fase 01 — Infraestructura · Hola Resuena 👋
      </span>
    </main>
  );
}
