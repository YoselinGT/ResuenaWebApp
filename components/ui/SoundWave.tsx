import { cn } from "@/lib/utils";

type SoundWaveProps = {
  bars?: number;
  className?: string;
  /** Altura del contenedor en px. */
  height?: number;
};

/**
 * Onda de sonido decorativa (barras animadas). Puramente estético —
 * marcado con aria-hidden. Usa la clase `.auth-wave-bar` de globals.css.
 */
export function SoundWave({ bars = 9, className, height = 40 }: SoundWaveProps) {
  return (
    <div
      aria-hidden
      className={cn("flex items-end justify-center gap-1", className)}
      style={{ height }}
    >
      {Array.from({ length: bars }).map((_, i) => (
        <span
          key={i}
          className="auth-wave-bar"
          style={
            {
              height: "100%",
              "--auth-wave-duration": `${0.9 + (i % 4) * 0.18}s`,
              "--auth-wave-delay": `${(i % 5) * 0.12}s`,
            } as React.CSSProperties
          }
        />
      ))}
    </div>
  );
}
