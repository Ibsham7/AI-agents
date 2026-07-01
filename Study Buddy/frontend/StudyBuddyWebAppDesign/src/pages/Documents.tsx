import React, { useState, useRef, useCallback, useEffect } from "react";
import { Upload, FileText, CheckCircle, Clock } from "lucide-react";
import { Screen, Doc } from "../types";
import { getDocuments, uploadDocument } from "../services/api";

export function DocumentsScreen({ onNavigate }: { onNavigate: (s: Screen) => void }) {
  const [isDragging, setIsDragging] = useState(false);
  const [docs, setDocs] = useState<Doc[]>([]);
  const [loading, setLoading] = useState(true);
  const fileRef = useRef<HTMLInputElement>(null);

  const fetchDocs = async () => {
    try {
      const data = await getDocuments();
      setDocs(data);
    } catch (e) {
      console.error("Failed to fetch documents", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocs();
    
    // Simple polling for document status
    const interval = setInterval(() => {
      fetchDocs();
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  const addDoc = useCallback(async (file: File) => {
    if (!file.name.endsWith(".pdf")) {
      alert("Only PDF files are supported");
      return;
    }
    
    try {
      await uploadDocument(file);
      await fetchDocs();
    } catch (e) {
      console.error("Failed to upload document", e);
      alert("Upload failed. Please try again.");
    }
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      const file = e.dataTransfer.files[0];
      if (file) addDoc(file);
    },
    [addDoc]
  );

  return (
    <div className="flex-1 overflow-y-auto p-6" style={{ scrollbarWidth: "none" }}>
      <div className="mb-8">
        <h1 className="text-2xl font-bold" style={{ color: "#1a191f" }}>
          Document Library
        </h1>
        <p className="text-sm mt-0.5" style={{ color: "#6b6b78" }}>
          Upload course materials and let AI tutor you on them
        </p>
      </div>

      {/* Drop zone */}
      <div
        className="rounded-2xl p-12 text-center mb-6 cursor-pointer transition-all"
        style={
          isDragging
            ? {
                border: "2px dashed #4f7296",
                background: "rgba(79,114,150,0.05)",
              }
            : {
                border: "2px dashed rgba(0,0,0,0.14)",
                background: "rgba(255,255,255,0.6)",
              }
        }
        onDragEnter={() => setIsDragging(true)}
        onDragLeave={() => setIsDragging(false)}
        onDragOver={(e) => e.preventDefault()}
        onDrop={handleDrop}
        onClick={() => fileRef.current?.click()}
        onMouseEnter={(e) => {
          if (!isDragging) e.currentTarget.style.background = "#ffffff";
        }}
        onMouseLeave={(e) => {
          if (!isDragging) e.currentTarget.style.background = "rgba(255,255,255,0.6)";
        }}
      >
        <input
          ref={fileRef}
          type="file"
          accept=".pdf"
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) addDoc(file);
          }}
        />
        <div
          className="w-16 h-16 rounded-2xl mx-auto mb-4 flex items-center justify-center transition-all"
          style={{
            background: isDragging ? "rgba(79,114,150,0.12)" : "rgba(0,0,0,0.05)",
          }}
        >
          <Upload
            className="w-7 h-7 transition-colors"
            style={{ color: isDragging ? "#4f7296" : "#9b9ba8" }}
          />
        </div>
        <p className="font-semibold mb-1" style={{ color: "#1a191f" }}>
          {isDragging ? "Drop to upload" : "Drag & drop your PDF here"}
        </p>
        <p className="text-sm" style={{ color: "#6b6b78" }}>
          or click to browse &nbsp;·&nbsp; PDF files up to 50 MB
        </p>
      </div>

      {/* File list */}
      <div
        className="rounded-2xl overflow-hidden"
        style={{
          background: "#ffffff",
          border: "1px solid rgba(0,0,0,0.07)",
          boxShadow: "0 1px 4px rgba(0,0,0,0.06)",
        }}
      >
        <div
          className="px-5 py-4 flex items-center justify-between"
          style={{ borderBottom: "1px solid rgba(0,0,0,0.07)" }}
        >
          <h2 className="font-semibold text-sm" style={{ color: "#1a191f" }}>
            Your Documents
          </h2>
          <span className="text-xs" style={{ color: "#6b6b78" }}>
            {docs.length} files
          </span>
        </div>
        <div>
          {docs.map((doc, i) => (
            <div
              key={doc.id}
              className="flex items-center gap-4 px-5 py-4 transition-all"
              style={{ borderTop: i > 0 ? "1px solid rgba(0,0,0,0.05)" : undefined }}
              onMouseEnter={(e) => (e.currentTarget.style.background = "#fafaf8")}
              onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
            >
              <div
                className="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0"
                style={{ background: "rgba(79,114,150,0.1)" }}
              >
                <FileText className="w-4 h-4" style={{ color: "#4f7296" }} />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate" style={{ color: "#1a191f" }}>
                  {doc.name}
                </p>
                <p className="text-xs" style={{ color: "#6b6b78" }}>
                  {doc.date} &nbsp;·&nbsp; {doc.size}
                </p>
              </div>
              {doc.status === "ready" ? (
                <span
                  className="flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-full font-medium"
                  style={{ color: "#16a34a", background: "rgba(22,163,74,0.1)" }}
                >
                  <CheckCircle className="w-3 h-3" />
                  Ready
                </span>
              ) : (
                <span
                  className="flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-full font-medium"
                  style={{ color: "#d97706", background: "rgba(217,119,6,0.1)" }}
                >
                  <Clock className="w-3 h-3 animate-spin" />
                  Processing
                </span>
              )}
              {doc.status === "ready" && (
                <button
                  onClick={() => onNavigate("chat")}
                  className="px-3 py-1.5 rounded-lg text-xs font-semibold transition-all"
                  style={{
                    color: "#4f7296",
                    background: "rgba(79,114,150,0.1)",
                    border: "1px solid rgba(79,114,150,0.2)",
                  }}
                  onMouseEnter={(e) => (e.currentTarget.style.background = "rgba(79,114,150,0.18)")}
                  onMouseLeave={(e) => (e.currentTarget.style.background = "rgba(79,114,150,0.1)")}
                >
                  Study
                </button>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
