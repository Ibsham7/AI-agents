import React, { useState, useRef, useEffect } from "react";
import { motion } from "motion/react";
import { HelpCircle, Check, X, FileText, Send } from "lucide-react";
import { ChatMessage, QuizData, Doc } from "../types";
import { Logo } from "../components/shared/Logo";
import { MarkdownText } from "../components/shared/MarkdownText";
import { sendMessage as apiSendMessage, submitQuizResult, getDocuments } from "../services/api";

function QuizCard({ quiz, onSubmit }: { quiz: QuizData & { topic?: string }; onSubmit: (correct: boolean, topic?: string) => void }) {
  const [selected, setSelected] = useState<number | null>(null);
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = () => {
    if (selected === null) return;
    setSubmitted(true);
    setTimeout(() => onSubmit(selected === quiz.correctIndex, quiz.topic), 500);
  };

  const optionStyle = (i: number): React.CSSProperties => {
    if (!submitted) {
      return selected === i
        ? { border: "1px solid #4f7296", background: "rgba(79,114,150,0.08)", color: "#1a191f" }
        : { border: "1px solid rgba(0,0,0,0.1)", background: "#ffffff", color: "#1a191f" };
    }
    if (i === quiz.correctIndex)
      return { border: "1px solid rgba(22,163,74,0.4)", background: "rgba(22,163,74,0.07)", color: "#16a34a" };
    if (i === selected)
      return { border: "1px solid rgba(220,38,38,0.4)", background: "rgba(220,38,38,0.07)", color: "#dc2626" };
    return { border: "1px solid rgba(0,0,0,0.06)", background: "#fafaf8", color: "#9b9ba8" };
  };

  return (
    <div
      className="rounded-2xl p-5 max-w-lg w-full"
      style={{
        background: "#ffffff",
        border: "1px solid rgba(79,114,150,0.2)",
        boxShadow: "0 2px 12px rgba(79,114,150,0.1)",
      }}
    >
      <div className="flex items-center gap-2 mb-4">
        <div
          className="w-6 h-6 rounded-lg flex items-center justify-center"
          style={{ background: "rgba(79,114,150,0.12)" }}
        >
          <HelpCircle className="w-3.5 h-3.5" style={{ color: "#4f7296" }} />
        </div>
        <span className="text-xs font-bold uppercase tracking-widest" style={{ color: "#4f7296" }}>
          Quick Quiz
        </span>
      </div>

      <p className="font-medium text-sm leading-relaxed mb-4" style={{ color: "#1a191f" }}>
        {quiz.question}
      </p>

      <div className="space-y-2 mb-4">
        {quiz.options.map((opt, i) => (
          <button
            key={i}
            onClick={() => !submitted && setSelected(i)}
            disabled={submitted}
            className="w-full text-left px-4 py-3 rounded-xl text-sm transition-all flex items-center gap-3"
            style={optionStyle(i)}
            onMouseEnter={(e) => {
              if (!submitted && selected !== i)
                e.currentTarget.style.background = "rgba(0,0,0,0.03)";
            }}
            onMouseLeave={(e) => {
              if (!submitted && selected !== i)
                e.currentTarget.style.background = "#ffffff";
            }}
          >
            <span
              className="w-5 h-5 rounded-full border flex items-center justify-center flex-shrink-0 text-[10px] font-bold"
              style={{ borderColor: "currentColor" }}
            >
              {submitted && i === quiz.correctIndex ? (
                <Check className="w-3 h-3" />
              ) : submitted && i === selected && i !== quiz.correctIndex ? (
                <X className="w-3 h-3" />
              ) : (
                String.fromCharCode(65 + i)
              )}
            </span>
            {opt}
          </button>
        ))}
      </div>

      {submitted ? (
        <div
          className="p-3.5 rounded-xl"
          style={{ background: "#f8f7f5", border: "1px solid rgba(0,0,0,0.07)" }}
        >
          <p className="text-xs leading-relaxed" style={{ color: "#6b6b78" }}>
            <span className="font-semibold" style={{ color: "#1a191f" }}>Explanation: </span>
            {quiz.explanation}
          </p>
        </div>
      ) : (
        <button
          onClick={handleSubmit}
          disabled={selected === null}
          className="w-full py-2.5 rounded-xl text-white text-sm font-semibold transition-all disabled:opacity-40"
          style={{ background: "#4f7296" }}
          onMouseEnter={(e) => (e.currentTarget.style.background = "#3d617f")}
          onMouseLeave={(e) => (e.currentTarget.style.background = "#4f7296")}
        >
          Submit Answer
        </button>
      )}
    </div>
  );
}

export function ChatScreen() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [docs, setDocs] = useState<Doc[]>([]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  
  // Use a simple random session ID for now, ideally persist it
  const sessionId = useRef(Math.random().toString(36).substring(7)).current;

  useEffect(() => {
    getDocuments().then(data => setDocs(data)).catch(console.error);
    
    // Initial greeting
    setMessages([{
      id: Date.now(),
      role: "ai",
      time: now(),
      content: "Hello! I'm your Study Buddy. How can I help you study today?"
    }]);
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  const now = () =>
    new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

  const sendMessage = async () => {
    if (!input.trim() || isTyping) return;
    const userMsg: ChatMessage = { id: Date.now(), role: "user", content: input, time: now() };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsTyping(true);
    
    try {
      const data = await apiSendMessage(userMsg.content, sessionId);
      
      const aiMsg: ChatMessage = {
        id: Date.now() + 1,
        role: "ai",
        content: data.response,
        time: now()
      };
      
      setMessages((prev) => [...prev, aiMsg]);
      
      if (data.quiz_triggered && data.quiz_data && data.quiz_data.questions.length > 0) {
        const q = data.quiz_data.questions[0];
        const options = q.options || [];
        const correctIndex = options.indexOf(q.answer);
        
        const quizMsg: ChatMessage = {
          id: Date.now() + 2,
          role: "quiz",
          time: now(),
          quiz: {
            topic: data.quiz_data.topic,
            question: q.question,
            options: options,
            correctIndex: correctIndex >= 0 ? correctIndex : 0,
            explanation: q.explanation || "No explanation provided."
          }
        };
        setMessages((prev) => [...prev, quizMsg]);
      }
    } catch (e) {
      console.error("Failed to send message", e);
      setMessages((prev) => [...prev, {
        id: Date.now() + 1,
        role: "ai",
        content: "Sorry, I'm having trouble connecting right now. Please try again later.",
        time: now()
      }]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleQuizSubmit = async (correct: boolean, topic?: string) => {
    if (topic) {
      try {
        await submitQuizResult(topic, correct);
      } catch (e) {
        console.error("Failed to submit quiz result", e);
      }
    }
    
    setMessages((prev) => [
      ...prev,
      {
        id: Date.now(),
        role: "ai",
        content: correct
          ? `🎉 Excellent! That's exactly right. Your progress in **${topic || 'the topic'}** has been recorded.`
          : `Good attempt! The correct answer was recorded. Want to try a follow-up question?`,
        time: now(),
      },
    ]);
  };

  return (
    <div className="flex-1 flex overflow-hidden">
      {/* Doc sidebar */}
      <div
        className="w-48 flex-shrink-0 flex flex-col"
        style={{ background: "#f5f4f0", borderRight: "1px solid rgba(0,0,0,0.07)" }}
      >
        <div
          className="px-4 py-3.5"
          style={{ borderBottom: "1px solid rgba(0,0,0,0.07)" }}
        >
          <h3
            className="text-xs font-bold uppercase tracking-widest"
            style={{ color: "#9b9ba8" }}
          >
            Active Document
          </h3>
        </div>
        <div className="p-3 space-y-1">
          {docs.length === 0 && (
            <p className="text-xs text-center p-2" style={{ color: "#6b6b78" }}>No documents uploaded yet.</p>
          )}
          {docs.filter((d) => d.status === "ready").map((doc, idx) => (
            <div
              key={doc.id}
              className="p-2.5 rounded-xl cursor-pointer transition-all"
              style={
                idx === 0
                  ? {
                      background: "rgba(79,114,150,0.1)",
                      border: "1px solid rgba(79,114,150,0.18)",
                    }
                  : { border: "1px solid transparent" }
              }
              onMouseEnter={(e) => {
                if (idx !== 0) e.currentTarget.style.background = "rgba(0,0,0,0.04)";
              }}
              onMouseLeave={(e) => {
                if (idx !== 0) e.currentTarget.style.background = "transparent";
              }}
            >
              <div className="flex items-center gap-2">
                <FileText
                  className="w-3.5 h-3.5 flex-shrink-0"
                  style={{ color: idx === 0 ? "#4f7296" : "#9b9ba8" }}
                />
                <p
                  className="text-xs font-medium truncate"
                  style={{ color: idx === 0 ? "#4f7296" : "#6b6b78" }}
                >
                  {doc.name.replace(".pdf", "")}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Main chat */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <div
          className="px-6 py-4 flex items-center gap-3"
          style={{ borderBottom: "1px solid rgba(0,0,0,0.07)", background: "#ffffff" }}
        >
          <div
            className="rounded-xl overflow-hidden flex-shrink-0"
            style={{ background: "#f4f5ef" }}
          >
            <Logo width={44} />
          </div>
          <div>
            <p className="text-sm font-semibold" style={{ color: "#1a191f" }}>
              Study Buddy AI
            </p>
            <p className="text-xs flex items-center gap-1.5" style={{ color: "#6b6b78" }}>
              <span
                className="w-1.5 h-1.5 rounded-full inline-block"
                style={{ background: "#16a34a" }}
              />
              Ready · ML Fundamentals
            </p>
          </div>
        </div>

        {/* Messages */}
        <div
          className="flex-1 overflow-y-auto px-6 py-5 space-y-4"
          style={{ scrollbarWidth: "none", background: "#eae8e3" }}
        >
          {messages.map((msg) => (
            <motion.div
              key={msg.id}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.22 }}
              className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
            >
              {msg.role === "quiz" && msg.quiz ? (
                <div className="flex gap-3 max-w-2xl w-full">
                  <div
                    className="rounded-lg overflow-hidden flex-shrink-0 mt-0.5"
                    style={{ background: "#f4f5ef", border: "1px solid rgba(0,0,0,0.08)" }}
                  >
                    <Logo width={36} />
                  </div>
                  <QuizCard quiz={msg.quiz} onSubmit={handleQuizSubmit} />
                </div>
              ) : msg.role === "ai" ? (
                <div className="flex gap-3 max-w-xl">
                  <div
                    className="rounded-lg overflow-hidden flex-shrink-0 mt-0.5"
                    style={{ background: "#f4f5ef", border: "1px solid rgba(0,0,0,0.08)" }}
                  >
                    <Logo width={36} />
                  </div>
                  <div>
                    <div
                      className="px-4 py-3 rounded-2xl rounded-tl-sm"
                      style={{
                        background: "#ffffff",
                        border: "1px solid rgba(0,0,0,0.08)",
                        color: "#1a191f",
                        boxShadow: "0 1px 3px rgba(0,0,0,0.06)",
                      }}
                    >
                      <MarkdownText text={msg.content ?? ""} />
                    </div>
                    <p className="text-xs mt-1.5 ml-1" style={{ color: "#9b9ba8" }}>
                      {msg.time}
                    </p>
                  </div>
                </div>
              ) : (
                <div className="max-w-sm">
                  <div
                    className="px-4 py-3 rounded-2xl rounded-tr-sm text-white text-sm leading-relaxed"
                    style={{
                      background: "#4f7296",
                      boxShadow: "0 2px 8px rgba(79,114,150,0.25)",
                    }}
                  >
                    {msg.content}
                  </div>
                  <p className="text-xs mt-1.5 text-right" style={{ color: "#9b9ba8" }}>
                    {msg.time}
                  </p>
                </div>
              )}
            </motion.div>
          ))}

          {isTyping && (
            <div className="flex gap-3">
              <div
                className="rounded-lg overflow-hidden flex-shrink-0"
                style={{ background: "#f4f5ef", border: "1px solid rgba(0,0,0,0.08)" }}
              >
                <Logo width={36} />
              </div>
              <div
                className="px-4 py-3.5 rounded-2xl rounded-tl-sm flex items-center gap-1.5"
                style={{
                  background: "#ffffff",
                  border: "1px solid rgba(0,0,0,0.08)",
                  boxShadow: "0 1px 3px rgba(0,0,0,0.06)",
                }}
              >
                {[0, 0.18, 0.36].map((delay, i) => (
                  <span
                    key={i}
                    className="w-1.5 h-1.5 rounded-full animate-bounce"
                    style={{ background: "#c4c4cc", animationDelay: `${delay}s` }}
                  />
                ))}
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {/* Input */}
        <div
          className="px-6 py-4"
          style={{ borderTop: "1px solid rgba(0,0,0,0.07)", background: "#ffffff" }}
        >
          <div
            className="flex items-center gap-3 px-4 py-3 rounded-2xl transition-all"
            style={{
              background: "#f5f4f0",
              border: "1px solid rgba(0,0,0,0.1)",
            }}
          >
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && sendMessage()}
              placeholder="Ask Study Buddy anything..."
              className="flex-1 bg-transparent text-sm outline-none"
              style={{ color: "#1a191f" }}
            />
            <button
              onClick={sendMessage}
              disabled={!input.trim() || isTyping}
              className="w-8 h-8 rounded-xl flex items-center justify-center text-white transition-all disabled:opacity-40"
              style={{ background: "#4f7296" }}
              onMouseEnter={(e) => (e.currentTarget.style.background = "#3d617f")}
              onMouseLeave={(e) => (e.currentTarget.style.background = "#4f7296")}
            >
              <Send className="w-3.5 h-3.5" />
            </button>
          </div>
          <p className="text-center text-xs mt-2" style={{ color: "#b4b4be" }}>
            Study Buddy can make mistakes. Verify important information.
          </p>
        </div>
      </div>
    </div>
  );
}
