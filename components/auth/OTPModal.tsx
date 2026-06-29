"use client";

import { useEffect, useRef, useState } from "react";
import { X } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/Button";
import { Alert } from "@/components/ui/Alert";
import { SoundWave } from "@/components/ui/SoundWave";

type Usuario = {
  id: string;
  nombre_completo: string;
  correo: string;
  tipo: string;
};

type Props = {
  preAuthSessionId: string;
  correo: string;
  onClose: () => void;
  onSuccess: (usuario: Usuario) => void;
};

const LEN = 6;

export function OTPModal({ preAuthSessionId, correo, onClose, onSuccess }: Props) {
  const [digits, setDigits] = useState<string[]>(Array(LEN).fill(""));
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [shake, setShake] = useState(false);
  const inputs = useRef<Array<HTMLInputElement | null>>([]);

  const code = digits.join("");

  useEffect(() => {
    inputs.current[0]?.focus();
  }, []);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [onClose]);

  function setDigit(i: number, value: string) {
    setError(null);
    const clean = value.replace(/\D/g, "");
    if (!clean) {
      setDigits((prev) => prev.map((d, idx) => (idx === i ? "" : d)));
      return;
    }
    setDigits((prev) => {
      const next = [...prev];
      // Permite pegar varios dígitos de una vez.
      const chars = clean.split("");
      let pos = i;
      for (const ch of chars) {
        if (pos >= LEN) break;
        next[pos] = ch;
        pos += 1;
      }
      const focusIdx = Math.min(pos, LEN - 1);
      requestAnimationFrame(() => inputs.current[focusIdx]?.focus());
      return next;
    });
  }

  function onKeyDown(i: number, e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Backspace" && !digits[i] && i > 0) {
      inputs.current[i - 1]?.focus();
    }
    if (e.key === "ArrowLeft" && i > 0) inputs.current[i - 1]?.focus();
    if (e.key === "ArrowRight" && i < LEN - 1) inputs.current[i + 1]?.focus();
  }

  async function submit(e?: React.FormEvent) {
    e?.preventDefault();
    if (code.length !== LEN || loading) return;
    setLoading(true);
    setError(null);
    try {
      const res = await api.post<{ usuario: Usuario }>("/auth/otp/verify", {
        pre_auth_session_id: preAuthSessionId,
        code,
      });
      onSuccess(res.usuario);
    } catch (err) {
      const msg =
        err instanceof ApiError
          ? err.status === 401
            ? "Código incorrecto. Verifica e inténtalo de nuevo."
            : err.message
          : "Ocurrió un error. Reintenta.";
      setError(msg);
      setShake(true);
      setTimeout(() => setShake(false), 450);
      setDigits(Array(LEN).fill(""));
      inputs.current[0]?.focus();
    } finally {
      setLoading(false);
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="otp-title"
    >
      <div
        className="absolute inset-0 bg-base/80 backdrop-blur-sm"
        onClick={onClose}
        aria-hidden
      />
      <div
        className={cn(
          "auth-enter relative w-full max-w-md rounded-lg border border-border bg-surface p-7 shadow-glow-lg",
          shake && "auth-shake",
        )}
      >
        <button
          type="button"
          onClick={onClose}
          aria-label="Cerrar"
          className="absolute right-4 top-4 text-text-muted transition-colors hover:text-text"
        >
          <X size={20} />
        </button>

        <SoundWave className="mb-5" height={32} />

        <h2 id="otp-title" className="text-center text-xl font-bold text-text">
          Verifica tu identidad
        </h2>
        <p className="mt-2 text-center text-sm text-text-muted">
          Enviamos un código de 6 dígitos a{" "}
          <span className="font-medium text-text">{correo}</span>
        </p>

        <form onSubmit={submit} className="mt-6 flex flex-col gap-5">
          <div className="flex justify-center gap-2" onPaste={() => setError(null)}>
            {digits.map((d, i) => (
              <input
                key={i}
                ref={(el) => {
                  inputs.current[i] = el;
                }}
                value={d}
                onChange={(e) => setDigit(i, e.target.value)}
                onKeyDown={(e) => onKeyDown(i, e)}
                inputMode="numeric"
                autoComplete={i === 0 ? "one-time-code" : "off"}
                maxLength={LEN}
                aria-label={`Dígito ${i + 1}`}
                className={cn(
                  "h-[52px] w-11 rounded-md border bg-surface-2 text-center text-xl font-semibold text-text",
                  "transition-all focus:outline-none focus:border-primary focus:ring-2 focus:ring-[var(--accent-glow)]",
                  error ? "border-danger" : "border-border",
                )}
              />
            ))}
          </div>

          {error && <Alert variant="error">{error}</Alert>}

          <Button type="submit" loading={loading} disabled={code.length !== LEN} fullWidth>
            Verificar y entrar
          </Button>
        </form>
      </div>
    </div>
  );
}
