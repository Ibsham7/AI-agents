import React, { useState, useEffect } from "react";
import {
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  ResponsiveContainer,
} from "recharts";
import { BookOpen, Target, Star, Zap, Bell, Plus, AlertTriangle, ChevronRight } from "lucide-react";
import { Screen, Topic } from "../types";
import { getStats } from "../services/api";
import { CircularProgress } from "../components/shared/CircularProgress";
import { auth } from "../lib/firebase";

const COLORS = ["#4f7296", "#d97706", "#16a34a", "#dc2626", "#0891b2", "#9333ea"];

function StatCard({
  label,
  value,
  icon: Icon,
  iconColor,
  sub,
}: {
  label: string;
  value: string;
  icon: React.ElementType;
  iconColor: string;
  sub?: string;
}) {
  return (
    <div
      className="rounded-2xl p-5 transition-all"
      style={{
        background: "#ffffff",
        boxShadow: "0 1px 4px rgba(0,0,0,0.07)",
        border: "1px solid rgba(0,0,0,0.07)",
      }}
    >
      <div className="flex items-start justify-between mb-3">
        <div
          className="w-9 h-9 rounded-xl flex items-center justify-center"
          style={{ background: `${iconColor}16` }}
        >
          <Icon className="w-4 h-4" style={{ color: iconColor }} />
        </div>
        {sub && (
          <span
            className="text-xs px-2 py-0.5 rounded-full font-medium"
            style={{ color: "#16a34a", background: "rgba(22,163,74,0.1)" }}
          >
            {sub}
          </span>
        )}
      </div>
      <div className="text-2xl font-bold" style={{ color: "#1a191f" }}>
        {value}
      </div>
      <div className="text-xs mt-0.5" style={{ color: "#6b6b78" }}>
        {label}
      </div>
    </div>
  );
}

export function DashboardScreen({ onNavigate }: { onNavigate: (s: Screen) => void }) {
  const [topics, setTopics] = useState<Topic[]>([]);
  const [totalSessions, setTotalSessions] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchStats() {
      try {
        const stats = await getStats();
        setTotalSessions(stats.total_sessions);
        const mappedTopics = stats.topics.map((t: any, idx: number) => ({
          name: t.topic,
          accuracy: Math.round(t.accuracy * 100),
          timesQuizzed: t.times_quizzed,
          needsReview: t.needs_review,
          color: COLORS[idx % COLORS.length]
        }));
        setTopics(mappedTopics);
      } catch (e) {
        console.error("Failed to fetch stats", e);
      } finally {
        setLoading(false);
      }
    }
    fetchStats();
  }, []);

  const needsReviewCount = topics.filter((t) => t.needsReview).length;
  const avgAccuracy = topics.length > 0 
    ? Math.round(topics.reduce((s, t) => s + t.accuracy, 0) / topics.length) 
    : 0;
  
  const radarData = topics.map(t => ({
    subject: t.name,
    score: t.accuracy,
    fullMark: 100
  }));

  const userDisplayName = auth.currentUser?.displayName || "Student";
  const today = new Date().toLocaleDateString("en-US", { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });

  return (
    <div className="flex-1 overflow-y-auto p-6" style={{ scrollbarWidth: "none" }}>
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold" style={{ color: "#1a191f" }}>
            Welcome back, {userDisplayName} 👋
          </h1>
          <p className="text-sm mt-0.5" style={{ color: "#6b6b78" }}>
            {today} · Keep up the great work!
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            className="w-9 h-9 rounded-xl flex items-center justify-center transition-all"
            style={{
              border: "1px solid rgba(0,0,0,0.1)",
              background: "#ffffff",
              color: "#6b6b78",
              boxShadow: "0 1px 3px rgba(0,0,0,0.06)",
            }}
            onMouseEnter={(e) => (e.currentTarget.style.color = "#1a191f")}
            onMouseLeave={(e) => (e.currentTarget.style.color = "#6b6b78")}
          >
            <Bell className="w-4 h-4" />
          </button>
          <button
            onClick={() => onNavigate("chat")}
            className="flex items-center gap-2 px-4 py-2 rounded-xl text-white text-sm font-semibold transition-all"
            style={{
              background: "#4f7296",
              boxShadow: "0 2px 8px rgba(79,114,150,0.3)",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = "#3d617f";
              e.currentTarget.style.boxShadow = "0 3px 10px rgba(79,114,150,0.35)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = "#4f7296";
              e.currentTarget.style.boxShadow = "0 2px 8px rgba(79,114,150,0.3)";
            }}
          >
            <Plus className="w-4 h-4" />
            New Session
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <StatCard label="Total Study Sessions" value={totalSessions.toString()} icon={BookOpen} iconColor="#4f7296" />
        <StatCard label="Average Accuracy" value={`${avgAccuracy}%`} icon={Target} iconColor="#16a34a" />
        <StatCard label="Topics Mastered" value={`${topics.filter(t => t.accuracy >= 80).length} / ${topics.length}`} icon={Star} iconColor="#d97706" />
        <StatCard label="Topics Tracking" value={topics.length.toString()} icon={Zap} iconColor="#0891b2" />
      </div>

      {/* Charts + Topic list */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-5">
        {/* Radar */}
        <div
          className="lg:col-span-2 rounded-2xl p-5"
          style={{
            background: "#ffffff",
            border: "1px solid rgba(0,0,0,0.07)",
            boxShadow: "0 1px 4px rgba(0,0,0,0.06)",
          }}
        >
          <h2 className="font-semibold text-sm mb-0.5" style={{ color: "#1a191f" }}>
            Topic Overview
          </h2>
          <p className="text-xs mb-4" style={{ color: "#6b6b78" }}>
            Accuracy across all subjects
          </p>
          <ResponsiveContainer width="100%" height={220}>
            {radarData.length > 0 ? (
              <RadarChart data={radarData} margin={{ top: 10, right: 24, bottom: 10, left: 24 }}>
                <PolarGrid stroke="rgba(0,0,0,0.08)" />
                <PolarAngleAxis dataKey="subject" tick={{ fill: "#6b6b78", fontSize: 10 }} />
                <Radar
                  name="Accuracy"
                  dataKey="score"
                  stroke="#4f7296"
                  fill="#4f7296"
                  fillOpacity={0.12}
                  strokeWidth={2}
                />
              </RadarChart>
            ) : (
              <div className="flex h-full items-center justify-center text-sm" style={{ color: "#6b6b78" }}>
                No topics yet. Start chatting to build your knowledge graph!
              </div>
            )}
          </ResponsiveContainer>
        </div>

        {/* Topic mastery list */}
        <div
          className="lg:col-span-3 rounded-2xl p-5"
          style={{
            background: "#ffffff",
            border: "1px solid rgba(0,0,0,0.07)",
            boxShadow: "0 1px 4px rgba(0,0,0,0.06)",
          }}
        >
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="font-semibold text-sm" style={{ color: "#1a191f" }}>
                Topic Mastery
              </h2>
              <p className="text-xs mt-0.5" style={{ color: needsReviewCount > 0 ? "#d97706" : "#6b6b78" }}>
                {needsReviewCount} topic{needsReviewCount !== 1 ? "s" : ""} need review
              </p>
            </div>
          </div>
          <div className="space-y-2">
            {topics.length === 0 ? (
              <div className="text-sm p-4 text-center" style={{ color: "#6b6b78" }}>
                Complete some quizzes in chat to see topics here.
              </div>
            ) : topics.map((topic) => (
              <div
                key={topic.name}
                className="flex items-center gap-4 px-3 py-2.5 rounded-xl transition-all cursor-pointer"
                style={
                  topic.needsReview
                    ? {
                        background: "rgba(220,38,38,0.04)",
                        border: "1px solid rgba(220,38,38,0.12)",
                      }
                    : { border: "1px solid transparent" }
                }
                onMouseEnter={(e) => {
                  if (!topic.needsReview)
                    e.currentTarget.style.background = "rgba(0,0,0,0.025)";
                }}
                onMouseLeave={(e) => {
                  if (!topic.needsReview)
                    e.currentTarget.style.background = "transparent";
                }}
              >
                <div className="relative flex-shrink-0">
                  <CircularProgress value={topic.accuracy} size={44} color={topic.color} />
                  <span
                    className="absolute inset-0 flex items-center justify-center text-[10px] font-bold"
                    style={{ color: "#1a191f" }}
                  >
                    {topic.accuracy}%
                  </span>
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium" style={{ color: "#1a191f" }}>
                      {topic.name}
                    </span>
                    {topic.needsReview && (
                      <span
                        className="flex items-center gap-1 text-[10px] font-semibold px-1.5 py-0.5 rounded-full"
                        style={{ color: "#d97706", background: "rgba(217,119,6,0.1)" }}
                      >
                        <AlertTriangle className="w-2.5 h-2.5" />
                        Review
                      </span>
                    )}
                  </div>
                  <p className="text-xs mt-0.5" style={{ color: "#6b6b78" }}>
                    Quizzed {topic.timesQuizzed} times
                  </p>
                </div>
                <button
                  onClick={() => onNavigate("chat")}
                  className="p-1 transition-colors"
                  style={{ color: "#9b9ba8" }}
                  onMouseEnter={(e) => (e.currentTarget.style.color = "#4f7296")}
                  onMouseLeave={(e) => (e.currentTarget.style.color = "#9b9ba8")}
                >
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
