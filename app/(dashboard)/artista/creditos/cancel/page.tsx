import Link from "next/link";
import { XCircle } from "lucide-react";
import { Button } from "@/components/ui/Button";

export default function CreditosCancelPage() {
  return (
    <div className="mx-auto mt-8 w-full max-w-md rounded-lg border border-border bg-surface p-8 text-center shadow-glow">
      <div
        className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-white/10 text-text-muted"
        aria-hidden
      >
        <XCircle size={30} />
      </div>
      <h1 className="text-xl font-bold text-text">Pago cancelado</h1>
      <p className="mt-2 text-sm text-text-muted">
        No se realizó ningún cargo. Puedes intentar la compra cuando quieras.
      </p>
      <Link href="/artista/creditos" className="mt-6 inline-block">
        <Button variant="secondary">Volver a créditos</Button>
      </Link>
    </div>
  );
}
