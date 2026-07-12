type Listener<T> = (value: T) => void;

function createConnection(sessionId: string) {
  let ws: WebSocket | null = null;
  let reconnectTimer: ReturnType<typeof setTimeout> | undefined;
  let started = false;

  const connectedListeners = new Set<Listener<boolean>>();
  const messageListeners = new Set<Listener<MessageEvent<string>>>();
  const errorListeners = new Set<Listener<Event>>();

  function notifyConnected(value: boolean) {
    for (const listener of connectedListeners) {
      listener(value);
    }
  }

  function notifyMessage(event: MessageEvent<string>) {
    for (const listener of messageListeners) {
      listener(event);
    }
  }

  function notifyError(event: Event) {
    for (const listener of errorListeners) {
      listener(event);
    }
  }

  function resolveUrl() {
    const loc = window.location;
    const isViteDev = ["5173", "5174", "5175"].includes(loc.port);
    const protocol = loc.protocol === "https:" ? "wss:" : "ws:";

    if (isViteDev) {
      return `ws://localhost:8000/ws/${sessionId}`;
    }

    return `${protocol}//${loc.host}/ws/${sessionId}`;
  }

  function connect() {
    if (!started) {
      return;
    }

    const url = resolveUrl();
    ws = new WebSocket(url);

    ws.onopen = () => {
      console.log("[WS] Connected", url);
      notifyConnected(true);
    };

    ws.onmessage = (event) => {
      notifyMessage(event);
    };

    ws.onclose = () => {
      notifyConnected(false);
      console.log("[WS] Disconnected, reconnecting in 2s...");
      reconnectTimer = setTimeout(connect, 2000);
    };

    ws.onerror = (event) => {
      console.error("[WS] Error:", event);
      notifyError(event);
    };
  }

  function start() {
    if (started) {
      return;
    }

    started = true;
    connect();
  }

  function stop() {
    started = false;
    clearTimeout(reconnectTimer);
    reconnectTimer = undefined;

    if (ws) {
      ws.onopen = null;
      ws.onmessage = null;
      ws.onclose = null;
      ws.onerror = null;
      ws.close();
      ws = null;
    }
  }

  function send(text: string) {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(text);
    }
  }

  return {
    start,
    stop,
    send,
    onConnected(listener: Listener<boolean>) {
      connectedListeners.add(listener);
      listener(Boolean(ws && ws.readyState === WebSocket.OPEN));
      return () => {
        connectedListeners.delete(listener);
      };
    },
    onMessage(listener: Listener<MessageEvent<string>>) {
      messageListeners.add(listener);
      return () => {
        messageListeners.delete(listener);
      };
    },
    onError(listener: Listener<Event>) {
      errorListeners.add(listener);
      return () => {
        errorListeners.delete(listener);
      };
    },
  };
}

const connections = new Map<string, ReturnType<typeof createConnection>>();

export function getConnection(sessionId: string) {
  if (!connections.has(sessionId)) {
    connections.set(sessionId, createConnection(sessionId));
  }

  return connections.get(sessionId)!;
}
