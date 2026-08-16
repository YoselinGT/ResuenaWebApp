"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { ChevronLeft, ChevronRight, Music, Image, Users, Send } from "lucide-react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Alert } from "@/components/ui/Alert";

type Genero = {
  id: number;
  nombre: string;
};

type Curador = {
  id: string;
  nombre_completo: string;
  canales: Array<{
    id: string;
    nombre: string;
    tipo: string;
    precio_creditos: number;
    descripcion_precio: string | null;
  }>;
};

type CampanaData = {
  id: string | null;
  titulo: string;
  descripcion: string;
  genero_id: number | null;
  audio_file: File | null;
  imagen_file: File | null;
  material_file: File | null;
  curadores_ids: string[];
};

const STEPS = [
  { key: "info", label: "Información", icon: Music },
  { key: "material", label: "Material", icon: Image },
  { key: "curadores", label: "Curadores", icon: Users },
  { key: "confirmar", label: "Confirmar", icon: Send },
];

export function CampanaWizard() {
  const router = useRouter();
  const [currentStep, setCurrentStep] = useState(0);
  const [generos, setGeneros] = useState<Genero[]>([]);
  const [curadores, setCuradores] = useState<Curador[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [creditosDisponibles, setCreditosDisponibles] = useState(0);

  const [data, setData] = useState<CampanaData>({
    id: null,
    titulo: "",
    descripcion: "",
    genero_id: null,
    audio_file: null,
    imagen_file: null,
    material_file: null,
    curadores_ids: [],
  });

  // Cargar géneros y curadores
  useEffect(() => {
    Promise.all([
      api.get<Genero[]>("/generos"),
      api.get<Curador[]>("/curadores/disponibles"),
      api.get<{ creditos_disponibles: number }>("/creditos/balance"),
    ])
      .then(([g, c, b]) => {
        setGeneros(g);
        setCuradores(c);
        setCreditosDisponibles(b.creditos_disponibles);
      })
      .catch(() => setError("No se pudieron cargar los datos."));
  }, []);

  const updateData = (updates: Partial<CampanaData>) => {
    setData((prev) => ({ ...prev, ...updates }));
  };

  // Guardar borrador (crear o actualizar)
  const saveDraft = async () => {
    if (!data.titulo || !data.genero_id) return;

    setLoading(true);
    setError(null);
    try {
      if (!data.id) {
        const res = await api.post<{ id: string }>("/campanas", {
          titulo: data.titulo,
          descripcion: data.descripcion || null,
          genero_id: data.genero_id,
        });
        updateData({ id: res.id });
      } else {
        await api.patch(`/campanas/${data.id}`, {
          titulo: data.titulo,
          descripcion: data.descripcion || null,
          genero_id: data.genero_id,
        });
      }
    } catch {
      setError("No se pudo guardar el borrador.");
    } finally {
      setLoading(false);
    }
  };

  // Subir archivos
  const uploadFiles = async () => {
    if (!data.id) return;

    setLoading(true);
    setError(null);
    try {
      if (data.audio_file) {
        const formData = new FormData();
        formData.append("file", data.audio_file);
        await api.post(`/campanas/${data.id}/upload/audio`, formData);
      }
      if (data.imagen_file) {
        const formData = new FormData();
        formData.append("file", data.imagen_file);
        await api.post(`/campanas/${data.id}/upload/imagen`, formData);
      }
      if (data.material_file) {
        const formData = new FormData();
        formData.append("file", data.material_file);
        await api.post(`/campanas/${data.id}/upload/material`, formData);
      }
    } catch {
      setError("No se pudieron subir los archivos.");
    } finally {
      setLoading(false);
    }
  };

  // Vincular curadores
  const linkCuradores = async () => {
    if (!data.id || data.curadores_ids.length === 0) return;

    setLoading(true);
    setError(null);
    try {
      await api.post(`/campanas/${data.id}/curadores`, {
        profesional_ids: data.curadores_ids,
      });
    } catch {
      setError("No se pudieron vincular los curadores.");
    } finally {
      setLoading(false);
    }
  };

  // Enviar campaña
  const handleSubmit = async () => {
    if (!data.id) return;

    setLoading(true);
    setError(null);
    try {
      const res = await api.post<{ status: string; creditos_faltantes?: number }>(
        `/campanas/${data.id}/enviar`
      );

      if (res.status === "sin_creditos") {
        setError(
          `No tienes créditos suficientes. Te faltan ${res.creditos_faltantes} créditos.`
        );
        return;
      }

      router.push(`/artista/campanas/${data.id}`);
    } catch {
      setError("No se pudo enviar la campaña.");
    } finally {
      setLoading(false);
    }
  };

  const nextStep = async () => {
    if (currentStep === 0) {
      await saveDraft();
    } else if (currentStep === 1) {
      await uploadFiles();
    } else if (currentStep === 2) {
      await linkCuradores();
    }

    if (currentStep < STEPS.length - 1) {
      setCurrentStep((prev) => prev + 1);
    }
  };

  const prevStep = () => {
    if (currentStep > 0) {
      setCurrentStep((prev) => prev - 1);
    }
  };

  const canAdvance = () => {
    switch (currentStep) {
      case 0:
        return data.titulo && data.genero_id;
      case 1:
        return data.audio_file || data.id; // Audio o ya guardado
      case 2:
        return data.curadores_ids.length > 0;
      default:
        return true;
    }
  };

  // Calcular créditos necesarios
  const creditosNecesarios = curadores
    .filter((c) => data.curadores_ids.includes(c.id))
    .reduce((sum, c) => {
      const precio = c.canales[0]?.precio_creditos || 1;
      return sum + precio;
    }, 0);

  return (
    <div className="mx-auto max-w-3xl">
      {/* Stepper */}
      <nav className="mb-8">
        <ol className="flex items-center gap-2">
          {STEPS.map((step, i) => {
            const Icon = step.icon;
            const isActive = i === currentStep;
            const isCompleted = i < currentStep;

            return (
              <li key={step.key} className="flex items-center gap-2">
                <div
                  className={`flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                    isActive
                      ? "bg-primary text-white"
                      : isCompleted
                        ? "bg-success/20 text-success"
                        : "bg-surface-2 text-text-muted"
                  }`}
                >
                  <Icon size={16} />
                  {step.label}
                </div>
                {i < STEPS.length - 1 && (
                  <ChevronRight size={16} className="text-text-muted" />
                )}
              </li>
            );
          })}
        </ol>
      </nav>

      {error && (
        <Alert variant="error" className="mb-6">
          {error}
        </Alert>
      )}

      {/* Contenido del paso */}
      <div className="rounded-lg border border-border bg-surface p-6">
        {currentStep === 0 && (
          <StepInfo
            data={data}
            generos={generos}
            onChange={updateData}
          />
        )}

        {currentStep === 1 && (
          <StepMaterial
            data={data}
            onChange={updateData}
          />
        )}

        {currentStep === 2 && (
          <StepCuradores
            curadores={curadores}
            selectedIds={data.curadores_ids}
            onChange={(ids) => updateData({ curadores_ids: ids })}
          />
        )}

        {currentStep === 3 && (
          <StepConfirmar
            data={data}
            generos={generos}
            curadores={curadores}
            creditosDisponibles={creditosDisponibles}
            creditosNecesarios={creditosNecesarios}
          />
        )}
      </div>

      {/* Navegación */}
      <div className="mt-6 flex items-center justify-between">
        <Button
          variant="ghost"
          onClick={prevStep}
          disabled={currentStep === 0}
        >
          <ChevronLeft size={16} />
          Anterior
        </Button>

        {currentStep < STEPS.length - 1 ? (
          <Button onClick={nextStep} disabled={!canAdvance()} loading={loading}>
            Siguiente
            <ChevronRight size={16} />
          </Button>
        ) : (
          <Button
            onClick={handleSubmit}
            loading={loading}
            disabled={creditosNecesarios > creditosDisponibles}
          >
            <Send size={16} />
            Enviar campaña
          </Button>
        )}
      </div>
    </div>
  );
}

// ── Sub-componentes ─────────────────────────────────────────────

function StepInfo({
  data,
  generos,
  onChange,
}: {
  data: CampanaData;
  generos: Genero[];
  onChange: (updates: Partial<CampanaData>) => void;
}) {
  return (
    <div className="flex flex-col gap-4">
      <h2 className="text-lg font-semibold text-text">Información básica</h2>

      <div>
        <label className="mb-1.5 block text-sm font-medium text-text-muted">
          Título de la campaña
        </label>
        <input
          type="text"
          value={data.titulo}
          onChange={(e) => onChange({ titulo: e.target.value })}
          placeholder="Ej: Nuevo single de reggaeton"
          className="w-full rounded-lg border border-border bg-surface-2 px-3 py-2 text-sm text-text placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-primary"
        />
      </div>

      <div>
        <label className="mb-1.5 block text-sm font-medium text-text-muted">
          Descripción (opcional)
        </label>
        <textarea
          value={data.descripcion}
          onChange={(e) => onChange({ descripcion: e.target.value })}
          placeholder="Describe tu campaña para los curadores..."
          rows={3}
          className="w-full rounded-lg border border-border bg-surface-2 px-3 py-2 text-sm text-text placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-primary"
        />
      </div>

      <div>
        <label className="mb-1.5 block text-sm font-medium text-text-muted">
          Género musical
        </label>
        <select
          value={data.genero_id || ""}
          onChange={(e) => onChange({ genero_id: Number(e.target.value) || null })}
          className="w-full rounded-lg border border-border bg-surface-2 px-3 py-2 text-sm text-text focus:outline-none focus:ring-2 focus:ring-primary"
        >
          <option value="">Selecciona un género</option>
          {generos.map((g) => (
            <option key={g.id} value={g.id}>
              {g.nombre}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
}

function StepMaterial({
  data,
  onChange,
}: {
  data: CampanaData;
  onChange: (updates: Partial<CampanaData>) => void;
}) {
  return (
    <div className="flex flex-col gap-4">
      <h2 className="text-lg font-semibold text-text">Material promocional</h2>

      <div>
        <label className="mb-1.5 block text-sm font-medium text-text-muted">
          Audio (MP3/WAV, máx 50MB)
        </label>
        <input
          type="file"
          accept=".mp3,.wav"
          onChange={(e) => onChange({ audio_file: e.target.files?.[0] || null })}
          className="w-full text-sm text-text-muted file:mr-4 file:rounded-lg file:border-0 file:bg-primary file:px-4 file:py-2 file:text-sm file:font-medium file:text-white hover:file:bg-primary/90"
        />
      </div>

      <div>
        <label className="mb-1.5 block text-sm font-medium text-text-muted">
          Imagen de portada (JPG/PNG, máx 5MB)
        </label>
        <input
          type="file"
          accept=".jpg,.jpeg,.png"
          onChange={(e) => onChange({ imagen_file: e.target.files?.[0] || null })}
          className="w-full text-sm text-text-muted file:mr-4 file:rounded-lg file:border-0 file:bg-primary file:px-4 file:py-2 file:text-sm file:font-medium file:text-white hover:file:bg-primary/90"
        />
      </div>

      <div>
        <label className="mb-1.5 block text-sm font-medium text-text-muted">
          Material adicional (ZIP, máx 100MB, opcional)
        </label>
        <input
          type="file"
          accept=".zip"
          onChange={(e) => onChange({ material_file: e.target.files?.[0] || null })}
          className="w-full text-sm text-text-muted file:mr-4 file:rounded-lg file:border-0 file:bg-primary file:px-4 file:py-2 file:text-sm file:font-medium file:text-white hover:file:bg-primary/90"
        />
      </div>
    </div>
  );
}

function StepCuradores({
  curadores,
  selectedIds,
  onChange,
}: {
  curadores: Curador[];
  selectedIds: string[];
  onChange: (ids: string[]) => void;
}) {
  const toggleCurador = (id: string) => {
    if (selectedIds.includes(id)) {
      onChange(selectedIds.filter((i) => i !== id));
    } else {
      onChange([...selectedIds, id]);
    }
  };

  return (
    <div className="flex flex-col gap-4">
      <h2 className="text-lg font-semibold text-text">Seleccionar curadores</h2>
      <p className="text-sm text-text-muted">
        Selecciona los curadores a los que quieres enviar tu campaña.
      </p>

      <div className="grid gap-3 sm:grid-cols-2">
        {curadores.map((curador) => {
          const isSelected = selectedIds.includes(curador.id);
          const precio = curador.canales[0]?.precio_creditos || 1;

          return (
            <button
              key={curador.id}
              type="button"
              onClick={() => toggleCurador(curador.id)}
              className={`rounded-lg border p-4 text-left transition-colors ${
                isSelected
                  ? "border-primary bg-primary/10"
                  : "border-border bg-surface-2 hover:border-primary/50"
              }`}
            >
              <p className="font-medium text-text">{curador.nombre_completo}</p>
              <p className="mt-1 text-xs text-text-muted">
                {curador.canales.length} canal(es) · {precio} crédito(s)
              </p>
            </button>
          );
        })}
      </div>

      {curadores.length === 0 && (
        <p className="text-center text-sm text-text-muted">
          No hay curadores disponibles en este momento.
        </p>
      )}
    </div>
  );
}

function StepConfirmar({
  data,
  generos,
  curadores,
  creditosDisponibles,
  creditosNecesarios,
}: {
  data: CampanaData;
  generos: Genero[];
  curadores: Curador[];
  creditosDisponibles: number;
  creditosNecesarios: number;
}) {
  const genero = generos.find((g) => g.id === data.genero_id);
  const curadoresSeleccionados = curadores.filter((c) =>
    data.curadores_ids.includes(c.id)
  );
  const tieneCreditos = creditosDisponibles >= creditosNecesarios;

  return (
    <div className="flex flex-col gap-4">
      <h2 className="text-lg font-semibold text-text">Confirmar envío</h2>

      <div className="rounded-lg border border-border bg-surface-2 p-4">
        <h3 className="font-medium text-text">{data.titulo}</h3>
        {data.descripcion && (
          <p className="mt-1 text-sm text-text-muted">{data.descripcion}</p>
        )}
        <p className="mt-2 text-xs text-text-muted">
          Género: {genero?.nombre || "No seleccionado"}
        </p>
      </div>

      <div>
        <h3 className="mb-2 font-medium text-text">Curadores seleccionados</h3>
        <ul className="space-y-2">
          {curadoresSeleccionados.map((c) => {
            const precio = c.canales[0]?.precio_creditos || 1;
            return (
              <li
                key={c.id}
                className="flex items-center justify-between rounded-lg border border-border bg-surface-2 px-3 py-2"
              >
                <span className="text-sm text-text">{c.nombre_completo}</span>
                <span className="text-sm font-medium text-primary">
                  {precio} crédito(s)
                </span>
              </li>
            );
          })}
        </ul>
      </div>

      <div className="rounded-lg border border-border bg-surface-2 p-4">
        <div className="flex items-center justify-between">
          <span className="text-sm text-text-muted">Créditos necesarios</span>
          <span className="font-medium text-text">{creditosNecesarios}</span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-sm text-text-muted">Créditos disponibles</span>
          <span
            className={`font-medium ${tieneCreditos ? "text-success" : "text-danger"}`}
          >
            {creditosDisponibles}
          </span>
        </div>
        {!tieneCreditos && (
          <p className="mt-2 text-sm text-danger">
            Te faltan {creditosNecesarios - creditosDisponibles} créditos.
          </p>
        )}
      </div>
    </div>
  );
}
