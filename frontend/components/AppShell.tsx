"use client";

import React, { useState, useEffect, useCallback, useRef } from "react";
import { Menu, X, WifiOff, Wifi } from "lucide-react";
import type { Session, Message } from "@/lib/types";
import { SessionSidebar } from "./SessionSidebar";
import { ChatMain } from "./ChatMain";
import { Button } from "@/components/ui/button";
import {
  generateId,
  createLoadingMessage,
  loadSessionsFromStorage,
  saveSessionsToStorage,
  cn,
} from "@/lib/utils";
import { sendChatMessage, checkHealth, getApiBase } from "@/lib/api";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function createSession(): Session {
  const now = new Date();
  return {
    id: generateId(),
    title: "Nuova sessione",
    createdAt: now,
    updatedAt: now,
    messages: [],
  };
}

function upsertMessage(sessions: Session[], sessionId: string, message: Message): Session[] {
  return sessions.map((s) => {
    if (s.id !== sessionId) return s;
    const exists = s.messages.find((m) => m.id === message.id);
    return {
      ...s,
      updatedAt: new Date(),
      messages: exists
        ? s.messages.map((m) => (m.id === message.id ? message : m))
        : [...s.messages, message],
    };
  });
}

function removeMessage(sessions: Session[], sessionId: string, messageId: string): Session[] {
  return sessions.map((s) => {
    if (s.id !== sessionId) return s;
    return { ...s, messages: s.messages.filter((m) => m.id !== messageId) };
  });
}

// ---------------------------------------------------------------------------
// Status bar (API health)
// ---------------------------------------------------------------------------

function ApiStatusBar({ apiBase }: { apiBase: string }) {
  const [online, setOnline] = useState<boolean | null>(null);

  useEffect(() => {
    let mounted = true;
    const check = async () => {
      const ok = await checkHealth();
      if (mounted) setOnline(ok);
    };
    check();
    const interval = setInterval(check, 30_000);
    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  if (online === null) return null;

  return (
    <div
      className={cn(
        "flex items-center gap-1.5 text-xs px-3 py-1 rounded",
        online
          ? "text-[var(--color-success)] bg-[var(--color-success-bg)]"
          : "text-[var(--color-error)] bg-[var(--color-error-bg)]"
      )}
      title={`API: ${apiBase}`}
      role="status"
      aria-live="polite"
    >
      {online ? (
        <><Wifi className="h-3 w-3" /> API connessa</>
      ) : (
        <><WifiOff className="h-3 w-3" /> API non raggiungibile</>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// AppShell
// ---------------------------------------------------------------------------

export function AppShell() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const isHydrated = useRef(false);

  // Load from localStorage on first render
  useEffect(() => {
    if (isHydrated.current) return;
    isHydrated.current = true;
    const saved = loadSessionsFromStorage();
    if (saved.length > 0) {
      setSessions(saved);
    }
  }, []);

  // Persist sessions whenever they change
  useEffect(() => {
    if (!isHydrated.current) return;
    saveSessionsToStorage(sessions);
  }, [sessions]);

  const activeSession = sessions.find((s) => s.id === activeId) ?? null;

  // ---------------------------------------------------------------------------
  // Session management
  // ---------------------------------------------------------------------------

  const handleNewSession = useCallback(() => {
    const session = createSession();
    setSessions((prev) => [session, ...prev]);
    setActiveId(session.id);
    setSidebarOpen(false);
  }, []);

  const handleSelectSession = useCallback((id: string) => {
    setActiveId(id);
    setSidebarOpen(false);
  }, []);

  const handleDeleteSession = useCallback((id: string) => {
    setSessions((prev) => prev.filter((s) => s.id !== id));
    setActiveId((prev) => (prev === id ? null : prev));
  }, []);

  // ---------------------------------------------------------------------------
  // Sending messages
  // ---------------------------------------------------------------------------

  const send = useCallback(
    async (text: string, pdf: File | null) => {
      if (isProcessing) return;

      // Ensure there's an active session
      let currentId = activeId;
      if (!currentId) {
        const session = createSession();
        setSessions((prev) => [session, ...prev]);
        setActiveId(session.id);
        currentId = session.id;
      }

      const sid = currentId;

      // Find or use existing backend session id
      const session = sessions.find((s) => s.id === sid);
      const backendSessionId = session?.backendSessionId;

      // Add user message
      const userMsg: Message = {
        id: generateId(),
        role: "user",
        content: text || (pdf ? `Documento: ${pdf.name}` : ""),
        attachedFileName: pdf?.name,
        timestamp: new Date(),
      };
      setSessions((prev) => upsertMessage(prev, sid, userMsg));

      // Add loading placeholder
      const loadingMsg = createLoadingMessage();
      setSessions((prev) => upsertMessage(prev, sid, loadingMsg));
      setIsProcessing(true);

      try {
        const result = await sendChatMessage({
          message: text || (pdf ? `Analizza il documento ${pdf.name}` : ""),
          sessionId: backendSessionId,
          pdf: pdf ?? undefined,
        });

        const assistantMsg: Message = {
          id: loadingMsg.id,
          role: "assistant",
          content: result.response,
          documentResult: result.document_result ?? undefined,
          timestamp: new Date(),
        };

        setSessions((prev) => {
          let updated = upsertMessage(prev, sid, assistantMsg);
          // Store backend session id for follow-ups
          if (result.session_id) {
            updated = updated.map((s) =>
              s.id === sid ? { ...s, backendSessionId: result.session_id } : s
            );
          }
          return updated;
        });
      } catch (err) {
        const errorMsg: Message = {
          id: loadingMsg.id,
          role: "assistant",
          content: "",
          error: err instanceof Error ? err.message : "Errore sconosciuto",
          timestamp: new Date(),
        };
        setSessions((prev) => upsertMessage(prev, sid, errorMsg));
      } finally {
        setIsProcessing(false);
      }
    },
    [activeId, isProcessing, sessions]
  );

  // Quick-send from dropzone (upload + auto-send)
  const handleDropzoneFileAndSend = useCallback(
    (file: File) => {
      send("", file);
    },
    [send]
  );

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------

  return (
    <div className="flex h-screen overflow-hidden" style={{ background: "var(--color-bg)" }}>
      {/* Sidebar — desktop fixed, mobile overlay */}
      <>
        {/* Mobile overlay backdrop */}
        {sidebarOpen && (
          <div
            className="fixed inset-0 z-20 bg-[var(--color-text)] opacity-20 sm:hidden"
            onClick={() => setSidebarOpen(false)}
            aria-hidden
          />
        )}

        {/* Sidebar panel */}
        <div
          className={cn(
            "fixed inset-y-0 left-0 z-30 w-64 flex flex-col border-r transition-transform duration-200 ease-out-quart sm:relative sm:translate-x-0 sm:z-auto sm:flex sm:shrink-0",
            sidebarOpen ? "translate-x-0" : "-translate-x-full sm:translate-x-0"
          )}
          style={{
            background: "var(--color-sidebar)",
            borderColor: "var(--color-border-subtle)",
          }}
        >
          <SessionSidebar
            sessions={sessions}
            activeId={activeId}
            onSelect={handleSelectSession}
            onNew={handleNewSession}
            onDelete={handleDeleteSession}
          />
        </div>
      </>

      {/* Main content */}
      <div className="flex flex-col flex-1 min-w-0">
        {/* Top bar */}
        <header
          className="flex items-center justify-between px-4 h-12 shrink-0 border-b"
          style={{
            background: "var(--color-surface)",
            borderColor: "var(--color-border-subtle)",
          }}
        >
          {/* Mobile menu toggle */}
          <Button
            variant="ghost"
            size="icon-sm"
            className="sm:hidden"
            onClick={() => setSidebarOpen((v) => !v)}
            aria-label="Menu sessioni"
          >
            {sidebarOpen ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
          </Button>

          {/* Title — hidden on desktop (sidebar has it) */}
          <span className="text-sm font-semibold text-[var(--color-text)] sm:hidden">
            DocumentAI
          </span>

          {/* Active session info — desktop */}
          <div className="hidden sm:flex items-center gap-2 text-sm text-[var(--color-text-secondary)]">
            {activeSession ? (
              <span className="truncate max-w-md">
                {activeSession.messages.find((m) => m.role === "user")?.attachedFileName ??
                  activeSession.messages.find((m) => m.role === "user")?.content?.slice(0, 60) ??
                  "Nuova sessione"}
              </span>
            ) : (
              <span className="text-[var(--color-text-tertiary)] text-xs">
                Seleziona o crea una sessione
              </span>
            )}
          </div>

          {/* API status */}
          <ApiStatusBar apiBase={getApiBase()} />
        </header>

        {/* Chat area */}
        <main className="flex-1 min-h-0">
          {activeId ? (
            <ChatMain
              session={activeSession}
              onSend={send}
              isProcessing={isProcessing}
              onDropzoneFile={() => {}}
              onDropzoneFileAndSend={handleDropzoneFileAndSend}
            />
          ) : (
            <NoSessionPlaceholder onNew={handleNewSession} onFile={handleDropzoneFileAndSend} />
          )}
        </main>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// No-session placeholder
// ---------------------------------------------------------------------------

function NoSessionPlaceholder({
  onNew,
  onFile,
}: {
  onNew: () => void;
  onFile: (file: File) => void;
}) {
  return (
    <div className="flex flex-col items-center justify-center h-full px-8 py-16 animate-fade-in">
      <div className="w-full max-w-sm space-y-6 text-center">
        <div>
          <h2 className="text-base font-semibold text-[var(--color-text)] mb-2">
            Nessuna sessione aperta
          </h2>
          <p className="text-sm text-[var(--color-text-secondary)]">
            Crea una nuova sessione per elaborare un documento Ercole o fare una domanda.
          </p>
        </div>
        <Button variant="primary" size="lg" onClick={onNew} className="w-full">
          Nuova sessione
        </Button>
        <p className="text-xs text-[var(--color-text-tertiary)]">
          Puoi anche trascinare un PDF direttamente qui.
        </p>
      </div>
    </div>
  );
}
