"use client";

import Link from "next/link";
import { Logo } from "@/components/ui/Logo";
import { SoundWave } from "@/components/ui/SoundWave";
import { Button } from "@/components/ui/Button";
import { useOnboardingProgress } from "@/hooks/useOnboardingProgress";

export default function CompletadoPage() {
  const { tipo } = useOnboardingProgress();

  return (
    <div className="auth-enter flex flex-col items-center text-center">
      <Logo width={160} priority className="mb-8" />

      <div
        className="auth-success-check mb-6 flex h-20 w-20 items-center justify-center rounded-full bg-success/15 text-4xl text-success"
        aria-hidden
      >
        ✓
      </div>

      <h1 className="text-2xl font-bold tracking-tight text-text sm:text-3xl">
        ¡Tu perfil está listo!
      </h1>
      <p className="mt-3 max-w-md text-sm leading-relaxed text-text-muted">
        Completaste tu onboarding. Ya configuramos tus preferencias para
        emparejarte con las campañas y curadores más afines.
        {tipo === "curador" &&
          " Si tu solicitud de curador sigue en revisión, te avisaremos por correo cuando sea aprobada."}
      </p>

      <SoundWave className="my-8" height={44} bars={11} />

      <div className="flex flex-wrap items-center justify-center gap-3">
        <Link href="/home">
          <Button size="lg">Ir a mi dashboard</Button>
        </Link>
        <Link href="/onboarding/generos">
          <Button size="lg" variant="ghost">
            Revisar mi perfil
          </Button>
        </Link>
      </div>
    </div>
  );
}
