import React, { useState, useEffect } from "react";
import { Screen } from "./types";
import { Sidebar } from "./components/layout/Sidebar";
import { AuthScreen } from "./pages/Auth";
import { DashboardScreen } from "./pages/Dashboard";
import { DocumentsScreen } from "./pages/Documents";
import { ChatScreen } from "./pages/Chat";
import { onAuthStateChanged, signOut, User } from "firebase/auth";
import { auth } from "./lib/firebase";

export default function App() {
  const [screen, setScreen] = useState<Screen>("dashboard");
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (currentUser) => {
      setUser(currentUser);
      setLoading(false);
    });
    return unsubscribe;
  }, []);

  if (loading) {
    return <div className="h-screen flex items-center justify-center">Loading...</div>;
  }

  if (!user) {
    return <AuthScreen />;
  }

  return (
    <div
      className="h-screen flex overflow-hidden"
      style={{ background: "#eae8e3", fontFamily: "'Inter', sans-serif" }}
    >
      <Sidebar
        screen={screen}
        onNavigate={setScreen}
        onLogout={() => {
          signOut(auth);
          setScreen("dashboard");
        }}
      />
      <main className="flex-1 flex overflow-hidden">
        {screen === "dashboard" && <DashboardScreen onNavigate={setScreen} />}
        {screen === "documents" && <DocumentsScreen onNavigate={setScreen} />}
        {screen === "chat" && <ChatScreen />}
      </main>
    </div>
  );
}
