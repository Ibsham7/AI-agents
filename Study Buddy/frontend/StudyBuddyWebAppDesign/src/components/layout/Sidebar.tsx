import React from "react";
import { Home, MessageSquare, FileText, LogOut } from "lucide-react";
import { Screen } from "../../types";
import { Logo } from "../shared/Logo";

export const NAV_ITEMS = [
  { id: "dashboard" as Screen, label: "Dashboard", icon: Home },
  { id: "chat" as Screen, label: "Study Chat", icon: MessageSquare },
  { id: "documents" as Screen, label: "Documents", icon: FileText },
];

export function Sidebar({
  screen,
  onNavigate,
  onLogout,
}: {
  screen: Screen;
  onNavigate: (s: Screen) => void;
  onLogout: () => void;
}) {
  return (
    <aside
      className="w-56 flex-shrink-0 flex flex-col"
      style={{
        background: "#f5f4f0",
        borderRight: "1px solid rgba(0,0,0,0.08)",
      }}
    >
      <div className="p-5 pb-3">
        <div className="flex items-center gap-2.5">
          <div className="rounded-lg overflow-hidden flex-shrink-0" style={{ background: "#f4f5ef" }}>
            <Logo width={40} />
          </div>
          <span className="font-bold text-base tracking-tight" style={{ color: "#1a191f" }}>
            Study Buddy
          </span>
        </div>
      </div>

      <nav className="flex-1 px-3 py-3 space-y-0.5">
        {NAV_ITEMS.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => onNavigate(id)}
            className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-150"
            style={
              screen === id
                ? {
                    background: "rgba(79,114,150,0.1)",
                    color: "#4f7296",
                    border: "1px solid rgba(79,114,150,0.15)",
                  }
                : { color: "#6b6b78", border: "1px solid transparent" }
            }
            onMouseEnter={(e) => {
              if (screen !== id) {
                e.currentTarget.style.background = "rgba(0,0,0,0.04)";
                e.currentTarget.style.color = "#1a191f";
              }
            }}
            onMouseLeave={(e) => {
              if (screen !== id) {
                e.currentTarget.style.background = "transparent";
                e.currentTarget.style.color = "#6b6b78";
              }
            }}
          >
            <Icon className="w-4 h-4" />
            {label}
          </button>
        ))}
      </nav>

      <div className="p-3" style={{ borderTop: "1px solid rgba(0,0,0,0.07)" }}>
        <div
          className="flex items-center gap-3 p-2 rounded-xl transition-all cursor-pointer"
          onMouseEnter={(e) => (e.currentTarget.style.background = "rgba(0,0,0,0.04)")}
          onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
        >
          <div
            className="w-8 h-8 rounded-full flex items-center justify-center text-white text-xs font-bold flex-shrink-0"
            style={{ background: "#4f7296" }}
          >
            AJ
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-xs font-semibold truncate" style={{ color: "#1a191f" }}>
              Alex Johnson
            </p>
            <p className="text-xs truncate" style={{ color: "#6b6b78" }}>
              alex@university.edu
            </p>
          </div>
          <button
            onClick={onLogout}
            className="p-1 transition-colors"
            style={{ color: "#9b9ba8" }}
            onMouseEnter={(e) => (e.currentTarget.style.color = "#1a191f")}
            onMouseLeave={(e) => (e.currentTarget.style.color = "#9b9ba8")}
          >
            <LogOut className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </aside>
  );
}
