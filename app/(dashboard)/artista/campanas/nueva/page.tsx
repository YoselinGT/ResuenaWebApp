"use client";

import { CampanaWizard } from "@/components/campanas/CampanaWizard";

export default function NuevaCampanaPage() {
  return (
    <div className="mx-auto flex w-full max-w-4xl flex-col gap-6 px-4 py-8">
      <header>
        <h1 className="text-2xl font-bold tracking-tight text-text">
          Nueva campaña
        </h1>
        <p className="mt-1 text-sm text-text-muted">
          Crea tu campaña musical paso a paso.
        </p>
      </header>

      <CampanaWizard />
    </div>
  );
}
