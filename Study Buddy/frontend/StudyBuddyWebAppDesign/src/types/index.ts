export type Screen = "auth" | "dashboard" | "chat" | "documents";
export type AuthMode = "signin" | "signup";
export type DocStatus = "ready" | "processing";
export type MessageRole = "user" | "ai" | "quiz";

export interface Topic {
  name: string;
  accuracy: number;
  timesQuizzed: number;
  needsReview: boolean;
  color: string;
}

export interface Doc {
  id: number;
  name: string;
  date: string;
  status: DocStatus;
  size: string;
}

export interface QuizData {
  question: string;
  options: string[];
  correctIndex: number;
  explanation: string;
}

export interface ChatMessage {
  id: number;
  role: MessageRole;
  content?: string;
  quiz?: QuizData;
  time: string;
}
