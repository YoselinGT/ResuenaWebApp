import Link from "next/link";
import { Logo } from "@/components/ui/Logo";
import { SoundWave } from "@/components/ui/SoundWave";
import { Button } from "@/components/ui/Button";

export default function HomePage() {
  return (
    <main className="auth-shell flex min-h-screen flex-col items-center justify-center gap-8 px-4 py-12 text-center">
      <Logo width={220} href={null} priority />
      <p className="max-w-md text-lg text-text-muted">
        Plataforma de gestión de campañas musicales. Conecta artistas con
        profesionales de la industria.
      </p>
      <SoundWave height={48} bars={13} />
      <div className="flex flex-wrap items-center justify-center gap-3">
        <Link href="/login">
          <Button size="lg">Iniciar sesión</Button>
        </Link>
        <Link href="/registro/artista">
          <Button size="lg" variant="secondary">
            Crear cuenta
          </Button>
        </Link>
      </div>
    </main>
  );
}
