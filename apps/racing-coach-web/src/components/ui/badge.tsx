import type { ReactNode } from 'react';
import { cn } from '@/lib/utils';

interface BadgeProps {
  children: ReactNode;
  variant?: 'default' | 'success' | 'warning' | 'danger' | 'info';
  className?: string;
}

const variantStyles = {
  default: 'bg-gray-800 text-gray-200',
  success: 'bg-green-900/30 text-green-400 border-green-800',
  warning: 'bg-yellow-900/30 text-yellow-400 border-yellow-800',
  danger: 'bg-red-900/30 text-red-400 border-red-800',
  info: 'bg-blue-900/30 text-blue-400 border-blue-800',
};

export function Badge({ children, variant = 'default', className }: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-md px-2 py-1 text-xs font-medium border',
        variantStyles[variant],
        className
      )}
    >
      {children}
    </span>
  );
}
