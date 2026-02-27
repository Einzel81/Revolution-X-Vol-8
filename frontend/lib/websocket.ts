// WebSocket connection manager with advanced features

type MessageHandler = (data: any) => void;
type ConnectionHandler = () => void;

interface WebSocketConfig {
  url: string;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
  heartbeatInterval?: number;
  channels?: string[];
}

class WebSocketManager {
  private ws: WebSocket | null = null;
  private config: WebSocketConfig;
  private messageHandlers: Map<string, MessageHandler[]> = new Map();
  private connectionHandlers: ConnectionHandler[] = [];
  private disconnectionHandlers: ConnectionHandler[] = [];
  private reconnectAttempts = 0;
  private reconnectTimer: NodeJS.Timeout | null = null;
  private heartbeatTimer: NodeJS.Timeout | null = null;
  private isIntentionallyClosed = false;

  constructor(config: WebSocketConfig) {
    this.config = {
      reconnectInterval: 5000,
      maxReconnectAttempts: 10,
      heartbeatInterval: 30000,
      ...config
    };
  }

  connect(): void {
    if (this.ws?.readyState === WebSocket.OPEN) return;

    this.isIntentionallyClosed = false;

    try {
      this.ws = new WebSocket(this.config.url);

      this.ws.onopen = this.handleOpen.bind(this);
      this.ws.onmessage = this.handleMessage.bind(this);
      this.ws.onerror = this.handleError.bind(this);
      this.ws.onclose = this.handleClose.bind(this);
    } catch (error) {
      console.error("WebSocket connection error:", error);
      this.scheduleReconnect();
    }
  }

  private handleOpen(): void {
    console.log("WebSocket connected");
    this.reconnectAttempts = 0;
    
    // Subscribe to channels
    if (this.config.channels && this.config.channels.length > 0) {
      this.send({
        action: "subscribe",
        channels: this.config.channels
      });
    }

    // Start heartbeat
    this.startHeartbeat();

    // Notify connection handlers
    this.connectionHandlers.forEach(handler => handler());
  }

  private handleMessage(event: MessageEvent): void {
    try {
      const data = JSON.parse(event.data);
      
      // Handle heartbeat response
      if (data.type === "pong") return;

      // Route message to handlers
      const handlers = this.messageHandlers.get(data.type) || [];
      handlers.forEach(handler => {
        try {
          handler(data.payload);
        } catch (error) {
          console.error("Error in message handler:", error);
        }
      });

      // Handle wildcard handlers
      const wildcardHandlers = this.messageHandlers.get("*") || [];
      wildcardHandlers.forEach(handler => {
        try {
          handler(data);
        } catch (error) {
          console.error("Error in wildcard handler:", error);
        }
      });
    } catch (error) {
      console.error("Error parsing WebSocket message:", error);
    }
  }

  private handleError(error: Event): void {
    console.error("WebSocket error:", error);
  }

  private handleClose(): void {
    console.log("WebSocket closed");
    this.stopHeartbeat();
    
    this.disconnectionHandlers.forEach(handler => handler());

    if (!this.isIntentionallyClosed) {
      this.scheduleReconnect();
    }
  }

  private scheduleReconnect(): void {
    if (this.reconnectAttempts >= (this.config.maxReconnectAttempts || 10)) {
      console.error("Max reconnection attempts reached");
      return;
    }

    this.reconnectAttempts++;
    const delay = Math.min(
      (this.config.reconnectInterval || 5000) * Math.pow(2, this.reconnectAttempts - 1),
      60000
    );

    console.log(`Reconnecting in ${delay}ms... (Attempt ${this.reconnectAttempts})`);

    this.reconnectTimer = setTimeout(() => {
      this.connect();
    }, delay);
  }

  private startHeartbeat(): void {
    this.heartbeatTimer = setInterval(() => {
      this.send({ type: "ping" });
    }, this.config.heartbeatInterval);
  }

  private stopHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }

  send(message: any): boolean {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
      return true;
    }
    return false;
  }

  on(type: string, handler: MessageHandler): () => void {
    if (!this.messageHandlers.has(type)) {
      this.messageHandlers.set(type, []);
    }
    this.messageHandlers.get(type)!.push(handler);

    // Return unsubscribe function
    return () => {
      const handlers = this.messageHandlers.get(type);
      if (handlers) {
        const index = handlers.indexOf(handler);
        if (index > -1) handlers.splice(index, 1);
      }
    };
  }

  onConnect(handler: ConnectionHandler): () => void {
    this.connectionHandlers.push(handler);
    return () => {
      const index = this.connectionHandlers.indexOf(handler);
      if (index > -1) this.connectionHandlers.splice(index, 1);
    };
  }

  onDisconnect(handler: ConnectionHandler): () => void {
    this.disconnectionHandlers.push(handler);
    return () => {
      const index = this.disconnectionHandlers.indexOf(handler);
      if (index > -1) this.disconnectionHandlers.splice(index, 1);
    };
  }

  disconnect(): void {
    this.isIntentionallyClosed = true;
    
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }

    this.stopHeartbeat();

    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}

// Singleton instance
let wsManager: WebSocketManager | null = null;

export function getWebSocketManager(config?: WebSocketConfig): WebSocketManager {
  if (!wsManager && config) {
    wsManager = new WebSocketManager(config);
  }
  return wsManager!;
}

export function createWebSocketManager(config: WebSocketConfig): WebSocketManager {
  return new WebSocketManager(config);
}

export { WebSocketManager };
export type { WebSocketConfig, MessageHandler, ConnectionHandler };
