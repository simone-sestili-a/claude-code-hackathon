"use client";

import React, { useEffect, useRef, useState, useCallback } from "react";
import { Send, Paperclip, X, AlertCircle, FileText } from "lucide-react";
import type { Message, Session } from "@/lib/types";
import { DocumentResult } from "./DocumentResult";
import { PdfDropzone } from "./PdfDropzone";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";

// ---------------------------------------------------------------------------
// Message components
// ---------------------------------------------------------------------------

function LoadingMessage() {
  return (
    <div
      className="animate-fade-in space-y-2 py-4"
      role="status"
      aria-label="Elaborazione in corso"
      aria-live="polite"
    >
      <Skeleton className="h-3.5 w-3/4" />
      <Skeleton className="h-3.5 w-1/2" />
      <Skeleton className="h-3.5 w-2/3" />
    </div>
  );
}

function UserMessage({ message }: { message: Message }) {
  return (
    <div className="flex justify-end animate-fade-in">
      <div
        className="max-w-xl rounded-md px-4 py-3 text-sm"
        style={{
          background: "var(--color-accent-subtle)",
          color: "var(--color-text)",
        }}
      >
        {message.attachedFileName && (
          <div className="flex items-center gap-1.5 mb-2 text-xs text-[var(--color-accent)] font-medium">
            <FileText className="h-3.5 w-3.5" />
            {message.attachedFileName}
          </div>
        )}
        <p className="leading-relaxed whitespace-pre-wrap">{message.content}</p>
      </div>
    </div>
  );
}

function AssistantMessage({ message }: { message: Message }) {
  if (message.error) {
    return (
      <div className="flex items-start gap-2.5 animate-fade-in">
        <div
          className="flex-1 rounded-md px-4 py-3 text-sm"
          style={{
            background: "var(--color-error-bg)",
            color: "var(--color-error)",
          }}
        >
          <div className="flex items-center gap-2 font-medium mb-1">
            <AlertCircle className="h-4 w-4" />
            Errore
          </div>
          <p className="text-[var(--color-text)]">{message.error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="animate-fade-in space-y-4 py-1">
      {/* Text response */}
      {message.content && (
        <p className="text-sm leading-relaxed text-[var(--color-text)] whitespace-pre-wrap">
          {message.content}
        </p>
      )}

      {/* Document result */}
      {message.documentResult && (
        <div
          className="rounded-md border p-5"
          style={{
            background: "var(--color-surface)",
            borderColor: "var(--color-border)",
          }}
        >
          <DocumentResult result={message.documentResult} />
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Empty state
// ---------------------------------------------------------------------------

function EmptyState({ onFile }: { onFile: (file: File | null) => void }) {
  return (
    <div className="flex-1 flex flex-col items-center justify-center px-8 py-16 animate-fade-in">
      <div className="w-full max-w-sm space-y-6">
        <div className="text-center">
          <h2 className="text-base font-semibold text-[var(--color-text)] mb-1">
            Elabora un documento Ercole
          </h2>
          <p className="text-sm text-[var(--color-text-secondary)]">
            Carica un PDF con i moduli di adesione, designazione o trasferimento.
            L&apos;AI identifica automaticamente i moduli e ne estrae i dati.
          </p>
        </div>
        <PdfDropzone file={null} onFile={onFile} />
        <p className="text-xs text-center text-[var(--color-text-tertiary)]">
          Puoi anche digitare una domanda o trascinare il PDF direttamente
          nell&apos;area di testo qui sotto.
        </p>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Input area
// ---------------------------------------------------------------------------

interface InputAreaProps {
  onSend: (text: string, pdf: File | null) => void;
  disabled: boolean;
  sessionHasMessages: boolean;
}

function InputArea({ onSend, disabled, sessionHasMessages }: InputAreaProps) {
  const [text, setText] = useState("");
  const [pdf, setPdf] = useState<File | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const canSend = (text.trim().length > 0 || pdf !== null) && !disabled;

  const handleSend = useCallback(() => {
    if (!canSend) return;
    onSend(text.trim(), pdf);
    setText("");
    setPdf(null);
    textareaRef.current?.focus();
  }, [canSend, text, pdf, onSend]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // Auto-resize textarea
  const handleTextChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setText(e.target.value);
    const el = e.target;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`;
  };

  const handleFilePick = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) setPdf(file);
    e.target.value = "";
  };

  // Drag-into-textarea
  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const file = Array.from(e.dataTransfer.files).find(
      (f) => f.type === "application/pdf"
    );
    if (file) setPdf(file);
  };

  return (
    <div
      className="px-4 py-4 border-t"
      style={{ borderColor: "var(--color-border-subtle)", background: "var(--color-bg)" }}
    >
      {/* PDF chip */}
      {pdf && (
        <div className="mb-2 flex items-center gap-2">
          <div className="flex items-center gap-1.5 rounded bg-[var(--color-accent-subtle)] px-2.5 py-1 text-xs text-[var(--color-accent)] font-medium">
            <FileText className="h-3.5 w-3.5" />
            <span className="max-w-xs truncate">{pdf.name}</span>
            <button
              type="button"
              onClick={() => setPdf(null)}
              className="ml-0.5 hover:opacity-60 transition-opacity"
              aria-label="Rimuovi PDF"
            >
              <X className="h-3 w-3" />
            </button>
          </div>
        </div>
      )}

      {/* Textarea row */}
      <div className="flex items-end gap-2">
        {/* Attach button */}
        <input
          ref={fileInputRef}
          type="file"
          accept="application/pdf"
          className="sr-only"
          onChange={handleFilePick}
          aria-label="Carica PDF"
        />
        <Button
          type="button"
          variant="ghost"
          size="icon-sm"
          onClick={() => fileInputRef.current?.click()}
          disabled={disabled}
          title="Allega PDF"
          aria-label="Allega PDF"
          className={cn(pdf ? "text-[var(--color-accent)]" : "")}
        >
          <Paperclip className="h-4 w-4" />
        </Button>

        {/* Text input */}
        <Textarea
          ref={textareaRef}
          value={text}
          onChange={handleTextChange}
          onKeyDown={handleKeyDown}
          onDrop={handleDrop}
          onDragOver={(e) => e.preventDefault()}
          placeholder={
            sessionHasMessages
              ? "Fai una domanda sul documento…"
              : "Scrivi un messaggio o trascina un PDF…"
          }
          disabled={disabled}
          rows={1}
          className="flex-1 min-h-[40px] max-h-40 py-2.5 resize-none overflow-y-auto text-sm"
          aria-label="Messaggio"
        />

        {/* Send button */}
        <Button
          type="button"
          variant="primary"
          size="icon"
          onClick={handleSend}
          disabled={!canSend}
          title="Invia (Enter)"
          aria-label="Invia messaggio"
        >
          <Send className="h-4 w-4" />
        </Button>
      </div>

      <p className="mt-1.5 text-[0.65rem] text-[var(--color-text-tertiary)] text-center">
        Invio con <kbd className="font-mono">Enter</kbd> · a capo con{" "}
        <kbd className="font-mono">Shift+Enter</kbd>
      </p>
    </div>
  );
}

// ---------------------------------------------------------------------------
// ChatMain
// ---------------------------------------------------------------------------

interface ChatMainProps {
  session: Session | null;
  onSend: (text: string, pdf: File | null) => void;
  isProcessing: boolean;
  onDropzoneFile: (file: File | null) => void;
  onDropzoneFileAndSend?: (file: File) => void;
}

export function ChatMain({
  session,
  onSend,
  isProcessing,
  onDropzoneFile,
  onDropzoneFileAndSend,
}: ChatMainProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const messages = session?.messages ?? [];
  const hasMessages = messages.length > 0;

  // Scroll to bottom when new messages arrive
  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    el.scrollTo({ top: el.scrollHeight, behavior: "smooth" });
  }, [messages.length]);

  const handleDropzoneFile = (file: File | null) => {
    if (file && onDropzoneFileAndSend) {
      onDropzoneFileAndSend(file);
    } else {
      onDropzoneFile(file);
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Message list or empty state */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 sm:px-8">
        {!hasMessages ? (
          <EmptyState onFile={handleDropzoneFile} />
        ) : (
          <div
            className="py-6 space-y-5 max-w-3xl mx-auto"
            aria-live="polite"
            aria-label="Conversazione"
          >
            {messages.map((msg) => (
              <React.Fragment key={msg.id}>
                {msg.isLoading ? (
                  <LoadingMessage />
                ) : msg.role === "user" ? (
                  <UserMessage message={msg} />
                ) : (
                  <AssistantMessage message={msg} />
                )}
              </React.Fragment>
            ))}
          </div>
        )}
      </div>

      {/* Input area */}
      <InputArea
        onSend={onSend}
        disabled={isProcessing}
        sessionHasMessages={hasMessages}
      />
    </div>
  );
}
