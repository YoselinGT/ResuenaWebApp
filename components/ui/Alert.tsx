import { AlertCircle, CheckCircle2, Info } from "lucide-react";
import { cn } from "@/lib/utils";

type AlertProps = {
  variant?: "error" | "success" | "info";
  children: React.ReactNode;
  className?: string;
};

const config = {
  error: {
    icon: AlertCircle,
    cls: "border-danger/40 bg-danger/10 text-danger",
    role: "alert" as const,
  },
  success: {
    icon: CheckCircle2,
    cls: "border-success/40 bg-success/10 text-success",
    role: "status" as const,
  },
  info: {
    icon: Info,
    cls: "border-primary/40 bg-primary/10 text-text",
    role: "status" as const,
  },
};

export function Alert({ variant = "info", children, className }: AlertProps) {
  const { icon: Icon, cls, role } = config[variant];
  return (
    <div
      role={role}
      className={cn(
        "flex items-start gap-2.5 rounded-md border px-3.5 py-3 text-sm",
        cls,
        className,
      )}
    >
      <Icon size={18} className="mt-0.5 shrink-0" />
      <div className="leading-snug">{children}</div>
    </div>
  );
}
