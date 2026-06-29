"use client";

import Link from "next/link";
import { Clock } from "lucide-react";
import { api } from "@/lib/api";
import { useRouter } from "next/navigation";
import { AuthCard } from "@/components/auth/AuthCard";
import { Button } from "@/components/ui/Button";
import { SoundWave } from "@/components/ui/SoundWave";

export default function PendientePage() {
  const router = useRouter();

  async function logout() {
    try {
      await api.post("/auth/logout");
    } catch {
      // Ignoramos errores: limpiamos sesión de todos modos.
    }
    router.push("/login");
  }

  return (
    <AuthCard title="Tu solicitud está en revisión">
      <div className="flex flex-col items-center text-center">
        <div
          className="mb-5 flex h-16 w-16 items-center justify-center rounded-full bg-primary/15 text-primary-light"
          aria-hidden
        >
          <Clock size={32} />
        </div>

        <p className="text-sm leading-relaxed text-text-muted">
          Recibimos tu solicitud de curador. Nuestro equipo la revisará y te
          avisaremos por correo cuando esté aprobada. Este proceso suele tomar
          poco tiempo.
        </p>

        <SoundWave className="my-7" height={34} />

        <div className="flex flex-col items-center gap-3">
          <Button variant="secondary" onClick={logout}>
            Cerrar sesión
          </Button>
          <Link
            href="/login"
            className="text-sm text-text-muted transition-colors hover:text-primary-light"
          >
            Volver a iniciar sesión
          </Link>
        </div>
      </div>
    </AuthCard>
  );
}
