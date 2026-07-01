import React, { useState } from "react";
import { motion } from "motion/react";
import { AuthMode } from "../types";
import { Logo } from "../components/shared/Logo";
import { 
  createUserWithEmailAndPassword, 
  signInWithEmailAndPassword, 
  signInWithPopup, 
  GoogleAuthProvider 
} from "firebase/auth";
import { auth } from "../lib/firebase";

export function AuthScreen() {
  const [mode, setMode] = useState<AuthMode>("signin");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const inputStyle: React.CSSProperties = {
    width: "100%",
    padding: "10px 14px",
    borderRadius: "10px",
    border: "1px solid rgba(0,0,0,0.15)",
    background: "#ffffff",
    color: "#1a191f",
    fontSize: "14px",
    outline: "none",
    transition: "border-color 0.15s",
  };

  const handleAuth = async () => {
    setError(null);
    setLoading(true);
    try {
      if (mode === "signup") {
        await createUserWithEmailAndPassword(auth, email, password);
        // Note: we can also update the user's profile with `name` if desired using updateProfile()
      } else {
        await signInWithEmailAndPassword(auth, email, password);
      }
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleAuth = async () => {
    setError(null);
    setLoading(true);
    try {
      const provider = new GoogleAuthProvider();
      await signInWithPopup(auth, provider);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      className="min-h-screen flex items-center justify-center p-4 w-full"
      style={{ background: "#eae8e3", fontFamily: "'Inter', sans-serif" }}
    >
      <motion.div
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.45, ease: [0.16, 1, 0.3, 1] }}
        className="w-full max-w-[420px]"
      >
        {/* Logo */}
        <div className="text-center mb-7">
          <div className="inline-flex items-center justify-center rounded-2xl mb-4 overflow-hidden"
            style={{ background: "#f4f5ef", boxShadow: "0 2px 12px rgba(0,0,0,0.1)" }}>
            <Logo width={120} />
          </div>
          <h1 className="text-[28px] font-bold tracking-tight" style={{ color: "#1a191f" }}>
            Study Buddy
          </h1>
          <p className="text-sm mt-1" style={{ color: "#6b6b78" }}>
            Your AI-powered learning companion
          </p>
        </div>

        {/* Card */}
        <div
          className="rounded-2xl p-8"
          style={{
            background: "#ffffff",
            boxShadow: "0 2px 16px rgba(0,0,0,0.08), 0 1px 4px rgba(0,0,0,0.04)",
          }}
        >
          {/* Tab switcher — underline style matching the reference */}
          <div
            className="flex mb-6"
            style={{ borderBottom: "1px solid rgba(0,0,0,0.1)" }}
          >
            {(["signin", "signup"] as const).map((m) => (
              <button
                key={m}
                onClick={() => {
                  setMode(m);
                  setError(null);
                }}
                className="flex-1 py-2.5 text-sm font-medium transition-all relative"
                style={{ color: mode === m ? "#4f7296" : "#6b6b78" }}
              >
                {m === "signin" ? "Sign In" : "Create Account"}
                {mode === m && (
                  <span
                    className="absolute bottom-0 left-0 right-0 h-0.5 rounded-full"
                    style={{ background: "#4f7296" }}
                  />
                )}
              </button>
            ))}
          </div>

          <div className="space-y-4">
            {error && (
              <div className="text-xs text-red-600 bg-red-50 p-3 rounded-lg">
                {error}
              </div>
            )}
            
            {mode === "signup" && (
              <div>
                <label className="block text-xs font-semibold mb-1.5" style={{ color: "#1a191f" }}>
                  Full Name
                </label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Alex Johnson"
                  style={inputStyle}
                  onFocus={(e) => (e.currentTarget.style.borderColor = "#4f7296")}
                  onBlur={(e) => (e.currentTarget.style.borderColor = "rgba(0,0,0,0.15)")}
                />
              </div>
            )}
            <div>
              <label className="block text-xs font-semibold mb-1.5" style={{ color: "#1a191f" }}>
                Email Address
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="alex@university.edu"
                style={inputStyle}
                onFocus={(e) => (e.currentTarget.style.borderColor = "#4f7296")}
                onBlur={(e) => (e.currentTarget.style.borderColor = "rgba(0,0,0,0.15)")}
              />
            </div>
            <div>
              <label className="block text-xs font-semibold mb-1.5" style={{ color: "#1a191f" }}>
                Password
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                style={inputStyle}
                onFocus={(e) => (e.currentTarget.style.borderColor = "#4f7296")}
                onBlur={(e) => (e.currentTarget.style.borderColor = "rgba(0,0,0,0.15)")}
              />
            </div>

            <button
              onClick={handleAuth}
              disabled={loading}
              className="w-full py-3 rounded-xl text-white text-sm font-semibold transition-all active:scale-[0.98] disabled:opacity-70"
              style={{ background: "#4f7296" }}
              onMouseEnter={(e) => (e.currentTarget.style.background = "#3d617f")}
              onMouseLeave={(e) => (e.currentTarget.style.background = "#4f7296")}
            >
              {loading ? "Please wait..." : (mode === "signin" ? "Sign In" : "Create Account")}
            </button>

            <div className="flex items-center gap-3 my-1">
              <div className="flex-1 h-px" style={{ background: "rgba(0,0,0,0.09)" }} />
              <span className="text-xs" style={{ color: "#6b6b78" }}>or continue with</span>
              <div className="flex-1 h-px" style={{ background: "rgba(0,0,0,0.09)" }} />
            </div>

            <button
              onClick={handleGoogleAuth}
              disabled={loading}
              className="w-full py-3 rounded-xl text-sm font-medium flex items-center justify-center gap-3 transition-all disabled:opacity-70"
              style={{
                border: "1px solid rgba(0,0,0,0.14)",
                background: "#ffffff",
                color: "#1a191f",
              }}
              onMouseEnter={(e) => (e.currentTarget.style.background = "#f8f7f5")}
              onMouseLeave={(e) => (e.currentTarget.style.background = "#ffffff")}
            >
              <svg width="18" height="18" viewBox="0 0 24 24">
                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
              </svg>
              Continue with Google
            </button>
          </div>
        </div>

        <p className="text-center text-xs mt-4" style={{ color: "#9b9ba8" }}>
          By continuing, you agree to our Terms of Service and Privacy Policy
        </p>
      </motion.div>
    </div>
  );
}
