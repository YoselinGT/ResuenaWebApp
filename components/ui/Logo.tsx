import Image from "next/image";
import Link from "next/link";
import { cn } from "@/lib/utils";

type LogoProps = {
  /** Ancho en px del logotipo completo. */
  width?: number;
  href?: string | null;
  className?: string;
  priority?: boolean;
};

export function Logo({
  width = 180,
  href = "/",
  className,
  priority = false,
}: LogoProps) {
  const img = (
    <Image
      src="/brand/logo-full.png"
      alt="Resuena"
      width={width}
      height={Math.round((width * 60) / 200)}
      priority={priority}
      className="h-auto w-auto select-none"
      style={{ width }}
    />
  );

  if (href) {
    return (
      <Link href={href} className={cn("inline-flex", className)} aria-label="Resuena — inicio">
        {img}
      </Link>
    );
  }
  return <span className={cn("inline-flex", className)}>{img}</span>;
}
