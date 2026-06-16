import type { HTMLAttributes } from "react";
import { cn } from "@/lib/utils";

export type CardProps = HTMLAttributes<HTMLDivElement>;

export function Card({ className, ...props }: CardProps) {
  return (
    <div
      className={cn(
        "rounded-md border border-border bg-surface shadow-xs",
        className,
      )}
      {...props}
    />
  );
}

export function CardHeader({ className, ...props }: CardProps) {
  return (
    <div
      className={cn(
        "flex items-center justify-between gap-4 border-b border-border px-6 py-4",
        className,
      )}
      {...props}
    />
  );
}

export function CardBody({ className, ...props }: CardProps) {
  return <div className={cn("p-6", className)} {...props} />;
}
