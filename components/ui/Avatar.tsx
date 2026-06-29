import { cn } from "@/lib/utils";

type AvatarProps = {
  name: string;
  src?: string | null;
  size?: number;
  className?: string;
};

/** Iniciales a partir del nombre (máx. 2 letras). */
function initials(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return "?";
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

/** Avatar circular: muestra la foto si existe, si no las iniciales. */
export function Avatar({ name, src, size = 36, className }: AvatarProps) {
  const dimension = { width: size, height: size };

  if (src) {
    return (
      // eslint-disable-next-line @next/next/no-img-element -- URL presigned remota; next/image requiere config de dominios
      <img
        src={src}
        alt={name}
        style={dimension}
        className={cn(
          "shrink-0 rounded-full border border-border object-cover",
          className,
        )}
      />
    );
  }

  return (
    <span
      style={dimension}
      aria-label={name}
      className={cn(
        "inline-flex shrink-0 select-none items-center justify-center rounded-full",
        "bg-primary/25 font-semibold text-primary-light",
        className,
      )}
    >
      <span style={{ fontSize: size * 0.4 }}>{initials(name)}</span>
    </span>
  );
}
