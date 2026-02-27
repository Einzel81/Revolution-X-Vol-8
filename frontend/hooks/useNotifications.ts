"use client";

import { useCallback, useEffect, useState } from "react";

//
// Types
//

export type NotificationType = "trade" | "price" | "system" | "ai";

export interface AppNotification {
  id: string;
  type: NotificationType;
  title: string;
  message: string;
  timestamp: string;
  read?: boolean;
}

export interface NotificationPreferences {
  filters: {
    trades: boolean;
    prices: boolean;
    system: boolean;
    ai: boolean;
  };
  sound: boolean;
  push: boolean;
}

//
// Helper: Map notification.type ? filters key
//

function mapNotificationTypeToFilterKey(
  t: NotificationType
): keyof NotificationPreferences["filters"] {
  switch (t) {
    case "trade":
      return "trades";
    case "price":
      return "prices";
    case "system":
      return "system";
    case "ai":
      return "ai";
    default:
      return "system";
  }
}

//
// Hook
//

export function useNotifications() {
  const [notifications, setNotifications] = useState<AppNotification[]>([]);
  const [preferences, setPreferences] = useState<NotificationPreferences>({
    filters: {
      trades: true,
      prices: true,
      system: true,
      ai: true,
    },
    sound: true,
    push: false,
  });

  //
  // Add notification
  //

  const addNotification = useCallback(
    (notification: AppNotification) => {
      const filterKey = mapNotificationTypeToFilterKey(notification.type);

      // Check filters safely
      if (!preferences.filters[filterKey]) return;

      setNotifications((prev) => [
        { ...notification, read: false },
        ...prev,
      ]);
    },
    [preferences.filters]
  );

  //
  // Mark as read
  //

  const markAsRead = useCallback((id: string) => {
    setNotifications((prev) =>
      prev.map((n) =>
        n.id === id ? { ...n, read: true } : n
      )
    );
  }, []);

  //
  // Clear all
  //

  const clearAll = useCallback(() => {
    setNotifications([]);
  }, []);

  //
  // Update preferences
  //

  const updatePreferences = useCallback(
    (newPrefs: Partial<NotificationPreferences>) => {
      setPreferences((prev) => ({
        ...prev,
        ...newPrefs,
        filters: {
          ...prev.filters,
          ...(newPrefs.filters ?? {}),
        },
      }));
    },
    []
  );

  //
  // Optional: Example WebSocket listener
  //

  useEffect(() => {
    // Example stub listener (replace with real WS if needed)
    // const ws = new WebSocket("wss://your-endpoint");

    // ws.onmessage = (event) => {
    //   const data: AppNotification = JSON.parse(event.data);
    //   addNotification(data);
    // };

    // return () => ws.close();
  }, [addNotification]);

  return {
    notifications,
    preferences,
    addNotification,
    markAsRead,
    clearAll,
    updatePreferences,
  };
}