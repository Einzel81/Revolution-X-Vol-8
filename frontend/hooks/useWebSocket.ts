"use client";

import { useEffect, useRef, useState, useCallback } from "react";

interface WebSocketMessage {
  type: string;
  payload: any;
  timestamp: number;
}

function buildWsUrl(): string {
  // 1) If explicitly provided, use it
  const envUrl = process.env.NEXT_PUBLIC_WS_URL;
  if (envUrl && envUrl.trim()) return envUrl.trim();

  // 2) Otherwise derive from current browser host:
  //    - Frontend is typically :3000
  //    - Backend is typically :8000
  if (typeof window !== "undefined") {
    const proto = window.location.protocol === "https:" ? "wss" : "ws";
    const host = window.location.hostname; // no port
    const backendPort = process.env.NEXT_PUBLIC_BACKEND_PORT || "8000";
    return `${proto}://${host}:${backendPort}/ws`;
  }

  // 3) SSR fallback
  return "ws://localhost:8000/ws";
}

export function useWebSocket() {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<string | null>(null);
  const [connectionError, setConnectionError] = useState<string | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 5;

  const connect = useCallback(() => {
    try {
      const wsUrl = buildWsUrl();
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        console.log("WebSocket connected:", wsUrl);
        setIsConnected(true);
        setConnectionError(null);
        reconnectAttempts.current = 0;

        // Optional subscribe (backend tolerates/ignores)
        ws.send(
          JSON.stringify({
            action: "subscribe",
            channels: ["price_updates", "trades", "alerts", "activities"],
          })
        );
      };

      ws.onmessage = (event) => {
        setLastMessage(event.data);
      };

      ws.onerror = (error) => {
        console.error("WebSocket error:", error);
        setConnectionError("Connection error occurred");
      };

      ws.onclose = () => {
        console.log("WebSocket disconnected");
        setIsConnected(false);

        if (reconnectAttempts.current < maxReconnectAttempts) {
          reconnectAttempts.current += 1;
          const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000);

          reconnectTimeoutRef.current = setTimeout(() => {
            console.log(`Reconnecting... Attempt ${reconnectAttempts.current}`);
            connect();
          }, delay);
        }
      };

      wsRef.current = ws;
    } catch (error) {
      console.error("Failed to create WebSocket:", error);
      setConnectionError("Failed to establish connection");
    }
  }, []);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  }, []);

  const sendMessage = useCallback((message: any) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
      return true;
    }
    return false;
  }, []);

  useEffect(() => {
    connect();
    return () => disconnect();
  }, [connect, disconnect]);

  return {
    isConnected,
    lastMessage,
    connectionError,
    sendMessage,
    reconnect: connect,
  };
}