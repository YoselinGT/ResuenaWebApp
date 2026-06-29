import { Logo } from "@/components/ui/Logo";
import { cn } from "@/lib/utils";

type AuthCardProps = {
  title: string;
  subtitle?: React.ReactNode;
  children: React.ReactNode;
  footer?: React.ReactNode;
  className?: string;
  /** Oculta el logo (p. ej. en pantallas que ya muestran un ícono grande). */
  hideLogo?: boolean;
};

export function AuthCard({
  title,
  subtitle,
  children,
  footer,
  className,
  hideLogo = false,
}: AuthCardProps) {
  return (
    <div className="auth-enter flex w-full max-w-md flex-col items-center">
      {!hideLogo && <Logo width={170} priority className="mb-8" />}
      <div
        className={cn(
          "w-full rounded-lg border border-border bg-surface p-7 shadow-glow sm:p-8",
          className,
        )}
      >
        <h1 className="text-2xl font-bold tracking-tight text-text">{title}</h1>
        {subtitle && (
          <p className="mt-2 text-sm leading-relaxed text-text-muted">{subtitle}</p>
        )}
        <div className="mt-6">{children}</div>
      </div>
      {footer && (
        <div className="mt-6 text-center text-sm text-text-muted">{footer}</div>
      )}
    </div>
  );
}
