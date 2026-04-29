import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-sm px-2 py-0.5 text-xs font-medium transition-colors duration-150",
  {
    variants: {
      variant: {
        default:
          "bg-[var(--color-accent-subtle)] text-[var(--color-accent)]",
        success:
          "bg-[var(--color-success-bg)] text-[var(--color-success)]",
        warning:
          "bg-[var(--color-warning-bg)] text-[var(--color-warning)]",
        error:
          "bg-[var(--color-error-bg)] text-[var(--color-error)]",
        neutral:
          "bg-[var(--color-sidebar)] text-[var(--color-text-secondary)]",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <span className={cn(badgeVariants({ variant }), className)} {...props} />
  );
}

export { Badge, badgeVariants };
