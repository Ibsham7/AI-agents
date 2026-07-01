import { auth } from "../lib/firebase";
import { Doc, Topic, ChatMessage, QuizData } from "../types";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function fetchWithAuth(endpoint: string, options: RequestInit = {}) {
  const user = auth.currentUser;
  if (!user) {
    throw new Error("User not authenticated");
  }

  const token = await user.getIdToken();
  const headers = new Headers(options.headers || {});
  headers.set("Authorization", `Bearer ${token}`);
  
  // Only set Content-Type to application/json if it's not a FormData request
  if (!(options.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`API Error (${response.status}): ${errorText}`);
  }

  return response.json();
}

export async function uploadDocument(file: File) {
  const formData = new FormData();
  formData.append("file", file);

  return fetchWithAuth("/docs/upload", {
    method: "POST",
    body: formData,
  });
}

export async function getDocuments(): Promise<Doc[]> {
  const data = await fetchWithAuth("/docs/");
  // Backend returns: id, filename, upload_date, status
  return data.map((doc: any) => ({
    id: doc.id,
    name: doc.filename,
    date: new Date(doc.upload_date).toLocaleDateString(),
    status: doc.status,
    size: "Unknown", // Backend doesn't return size currently
  }));
}

export async function getStats() {
  const data = await fetchWithAuth("/user/stats");
  // Expected response: { total_sessions: int, topics: [...] }
  return data;
}

export async function sendMessage(message: string, sessionId: string) {
  return fetchWithAuth("/chat/message", {
    method: "POST",
    body: JSON.stringify({
      message,
      session_id: sessionId,
    }),
  });
}

export async function submitQuizResult(topic: string, correct: boolean) {
  return fetchWithAuth("/quiz/result", {
    method: "POST",
    body: JSON.stringify({
      topic,
      correct,
    }),
  });
}
