import { useEffect, useCallback } from "react";
import { getConnection } from "../connection";
import { useHudStore } from "../store";

export function useWebSocket(sessionId: string = "default") {
  const { setConnected, addA2UIMessages, addHistory, setProcessing } = useHudStore();
  const connection = getConnection(sessionId);

  useEffect(() => {
    connection.start();

    const unsubscribeConnected = connection.onConnected((value) => {
      setConnected(value);
      if (!value) {
        setProcessing(false);
      }
    });

    const unsubscribeMessage = connection.onMessage((event) => {
      try {
        const data = JSON.parse(event.data);

        if (data?.channel === "a2ui" && Array.isArray(data.messages)) {
          addA2UIMessages(data.messages);
          setProcessing(false);
          return;
        }

        if (data?.channel === "event") {
          if (data.type === "connected") {
            console.log("[WS] session connected", data.data);
            return;
          }

          if (data.type === "processing") {
            setProcessing(true);
            return;
          }

          if (data.type === "reply") {
            const content = data?.data?.content || "";
            const source = data?.data?.source || "local";
            const payment = data?.data?.payment || null;
            if (content) {
              addHistory({ role: "assistant", text: content, source, payment });
            }
            setProcessing(false);
            return;
          }

          if (data.type === "error") {
            addHistory({ role: "assistant", text: `[Error] ${data?.data?.message || "unknown error"}` });
            setProcessing(false);
            return;
          }

          return;
        }

        if (data?.type === "chat_response") {
          const source = data.source || "local";
          const payment = data.payment || null;
          addHistory({ role: "assistant", text: data.reply || "", source, payment });
          if (data.a2ui_messages?.length) {
            addA2UIMessages(data.a2ui_messages);
          }
          setProcessing(false);
          return;
        }

        console.log("[WS] unhandled message", data);
      } catch (error) {
        console.error("[WS] Parse error:", error);
      }
    });

    const unsubscribeError = connection.onError(() => {
      setProcessing(false);
    });

    return () => {
      unsubscribeConnected();
      unsubscribeMessage();
      unsubscribeError();
      connection.stop();
    };
  }, [sessionId, connection, setConnected, addA2UIMessages, addHistory, setProcessing]);

  const sendMessage = useCallback(
    (text: string) => {
      if (!text.trim()) {
        return;
      }

      connection.send(text);
      addHistory({ role: "user", text });
      setProcessing(true);
    },
    [connection, addHistory, setProcessing]
  );

  return { sendMessage };
}