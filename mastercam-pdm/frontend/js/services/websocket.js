// frontend/js/services/websocket.js

import { setState, getState } from "../state/store.js";

let ws = null;
let reconnectAttempts = 0;
const MAX_RECONNECT_ATTEMPTS = 5;

function handleMessage(event) {
  try {
    const data = JSON.parse(event.data);
    console.log("WebSocket message received:", data.type);

    if (data.type === "FILE_LIST_UPDATED") {
      // Instead of calling a render function, we just update the state.
      // The UI will react automatically because it is subscribed to the store.
      setState({ groupedFiles: data.payload || {} });
    } else if (data.type === "NEW_MESSAGES") {
      // TODO: We can add a 'messages' array to our state store
      // and update it here, causing a message modal to appear.
      console.log("Received new messages:", data.payload);
    }
  } catch (error) {
    console.error("Error handling WebSocket message:", error);
  }
}

export function connectWebSocket() {
  if (ws && ws.readyState === WebSocket.OPEN) {
    console.log("WebSocket already connected.");
    return;
  }

  const { currentUser } = getState();
  if (!currentUser) {
    console.error("Cannot connect WebSocket without a current user.");
    return;
  }

  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const wsUrl = `${protocol}//${
    window.location.host
  }/ws?user=${encodeURIComponent(currentUser)}`;

  ws = new WebSocket(wsUrl);

  ws.onopen = () => {
    console.log("WebSocket connected successfully.");
    reconnectAttempts = 0;
    // Optionally send a message to confirm user identity
    ws.send(`SET_USER:${currentUser}`);
  };

  ws.onmessage = handleMessage;

  ws.onclose = () => {
    console.log("WebSocket disconnected.");
    if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
      const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 30000);
      setTimeout(() => {
        reconnectAttempts++;
        console.log(
          `Attempting to reconnect (attempt ${reconnectAttempts})...`
        );
        connectWebSocket();
      }, delay);
    } else {
      console.error("Max WebSocket reconnect attempts reached.");
      // We could update the state here to show a "Disconnected" banner in the UI
    }
  };

  ws.onerror = (error) => {
    console.error("WebSocket error:", error);
    ws.close();
  };
}

export function disconnectWebSocket() {
  if (ws) {
    reconnectAttempts = MAX_RECONNECT_ATTEMPTS; // Prevent reconnection
    ws.close();
    ws = null;
  }
}
