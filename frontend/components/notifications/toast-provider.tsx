"use client";

import React, { createContext, useContext, useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { 
  X, 
  CheckCircle, 
  AlertTriangle, 
  Info, 
  AlertCircle,
  Bell
} from "lucide-react";
import { Button } from "@/components/ui/button";

type ToastType = "success" | "error" | "warning" | "info";

interface Toast {
  id: string;
  type: ToastType;
  title: string;
  message: string;
  duration?: number;
  action?: {
    label: string;
    onClick: () => void;
  };
}

interface ToastContextType {
  toasts: Toast[];
  addToast: (toast: Omit<Toast, "id">) => void;
  removeToast: (id: string) => void;
  success: (title: string, message: string, action?: Toast["action"]) => void;
  error: (title: string, message: string, action?: Toast["action"]) => void;
  warning: (title: string, message: string, action?: Toast["action"]) => void;
  info: (title: string, message: string, action?: Toast["action"]) => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const addToast = useCallback((toast: Omit<Toast, "id">) => {
    const id = Math.random().toString(36).substring(2, 9);
    const newToast = { ...toast, id };
    
    setToasts((prev) => [...prev, newToast]);

    if (toast.duration !== 0) {
      setTimeout(() => {
        removeToast(id);
      }, toast.duration || 5000);
    }
  }, []);

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const success = useCallback((title: string, message: string, action?: Toast["action"]) => {
    addToast({ type: "success", title, message, action });
  }, [addToast]);

  const error = useCallback((title: string, message: string, action?: Toast["action"]) => {
    addToast({ type: "error", title, message, action });
  }, [addToast]);

  const warning = useCallback((title: string, message: string, action?: Toast["action"]) => {
    addToast({ type: "warning", title, message, action });
  }, [addToast]);

  const info = useCallback((title: string, message: string, action?: Toast["action"]) => {
    addToast({ type: "info", title, message, action });
  }, [addToast]);

  const getIcon = (type: ToastType) => {
    switch (type) {
      case "success":
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case "error":
        return <AlertCircle className="w-5 h-5 text-red-500" />;
      case "warning":
        return <AlertTriangle className="w-5 h-5 text-yellow-500" />;
      case "info":
        return <Info className="w-5 h-5 text-blue-500" />;
    }
  };

  const getStyles = (type: ToastType) => {
    switch (type) {
      case "success":
        return "border-green-500/30 bg-green-500/10";
      case "error":
        return "border-red-500/30 bg-red-500/10";
      case "warning":
        return "border-yellow-500/30 bg-yellow-500/10";
      case "info":
        return "border-blue-500/30 bg-blue-500/10";
    }
  };

  return (
    <ToastContext.Provider value={{ toasts, addToast, removeToast, success, error, warning, info }}>
      {children}
      
      {/* Toast Container */}
      <div className="fixed top-4 left-4 z-50 flex flex-col gap-2 pointer-events-none">
        <AnimatePresence>
          {toasts.map((toast) => (
            <motion.div
              key={toast.id}
              initial={{ opacity: 0, x: -50, scale: 0.9 }}
              animate={{ opacity: 1, x: 0, scale: 1 }}
              exit={{ opacity: 0, x: -50, scale: 0.9 }}
              className={`pointer-events-auto min-w-[350px] max-w-[450px] p-4 rounded-lg border backdrop-blur-xl shadow-xl ${getStyles(toast.type)}`}
            >
              <div className="flex items-start gap-3">
                <div className="mt-0.5">{getIcon(toast.type)}</div>
                <div className="flex-1">
                  <h4 className="font-semibold text-white text-sm">{toast.title}</h4>
                  <p className="text-slate-300 text-xs mt-1">{toast.message}</p>
                  
                  {toast.action && (
                    <Button
                      size="sm"
                      variant="ghost"
                      className="mt-2 h-7 text-xs"
                      onClick={() => {
                        toast.action?.onClick();
                        removeToast(toast.id);
                      }}
                    >
                      {toast.action.label}
                    </Button>
                  )}
                </div>
                <button
                  onClick={() => removeToast(toast.id)}
                  className="text-slate-400 hover:text-white transition-colors"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error("useToast must be used within ToastProvider");
  }
  return context;
}
