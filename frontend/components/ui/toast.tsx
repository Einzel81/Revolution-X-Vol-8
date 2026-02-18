'use client';

import * as React from 'react';
import { X, CheckCircle2, AlertCircle, Info } from 'lucide-react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';

const toastVariants = cva(
  "group pointer-events-auto relative flex w-full items-center justify-between space-x-4 overflow-hidden rounded-lg border p-6 pr-8 shadow-lg transition-all data-[swipe=cancel]:translate-x-0 data-[swipe=end]:translate-x-[var(--radix-toast-swipe-end-x)] data-[swipe=move]:translate-x-[var(--radix-toast-swipe-move-x)] data-[swipe=move]:transition-none data-[state=open]:animate-in data-[state=closed]:animate-out data-[swipe=end]:animate-out data-[state=closed]:fade-out-80 data-[state=closed]:slide-out-to-right-full data-[state=open]:slide-in-from-top-full data-[state=open]:sm:slide-in-from-bottom-full",
  {
    variants: {
      variant: {
        default: "border-gray-800 bg-gray-900 text-white",
        destructive: "border-red-500/30 bg-red-500/10 text-red-500",
        success: "border-green-500/30 bg-green-500/10 text-green-500",
        warning: "border-yellow-500/30 bg-yellow-500/10 text-yellow-500",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
);

export interface ToastProps extends React.HTMLAttributes<HTMLDivElement>, VariantProps<typeof toastVariants> {
  onDismiss?: () => void;
  title?: string;
  description?: string;
  action?: React.ReactNode;
}

export function Toast({ 
  className, 
  variant, 
  title, 
  description, 
  action,
  onDismiss,
  ...props 
}: ToastProps) {
  const icons = {
    default: Info,
    destructive: AlertCircle,
    success: CheckCircle2,
    warning: AlertCircle,
  };

  const Icon = icons[variant || 'default'];

  return (
    <div className={cn(toastVariants({ variant }), className)} {...props}>
      <div className="flex gap-3 w-full">
        <Icon className="w-5 h-5 shrink-0 mt-0.5" />
        <div className="flex-1 grid gap-1">
          {title && <div className="text-sm font-semibold">{title}</div>}
          {description && <div className="text-sm opacity-90">{description}</div>}
        </div>
      </div>
      {action && <div className="flex gap-2 mt-4">{action}</div>}
      {onDismiss && (
        <button
          onClick={onDismiss}
          className="absolute right-2 top-2 rounded-md p-1 text-gray-400 opacity-0 transition-opacity hover:text-white focus:opacity-100 focus:outline-none focus:ring-2 group-hover:opacity-100"
        >
          <X className="h-4 w-4" />
        </button>
      )}
    </div>
  );
}

export function ToastProvider({ children }: { children: React.ReactNode }) {
  return (
    <div className="fixed top-0 z-[100] flex max-h-screen w-full flex-col-reverse p-4 sm:bottom-0 sm:right-0 sm:top-auto sm:flex-col md:max-w-[420px] gap-2">
      {children}
    </div>
  );
}

export function useToast() {
  const [toasts, setToasts] = React.useState<Array<{ id: string; props: ToastProps }>>([]);

  const toast = React.useCallback(({ ...props }: ToastProps) => {
    const id = Math.random().toString(36).substring(7);
    setToasts((prev) => [...prev, { id, props }]);
    
    // Auto dismiss after 5 seconds
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 5000);
  }, []);

  const dismiss = React.useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  return {
    toast,
    toasts,
    dismiss,
  };
}
