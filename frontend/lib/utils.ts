import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";
import type { Contact, Session, Message } from "./types";

export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

export function generateId(): string {
  return Math.random().toString(36).slice(2, 10) + Date.now().toString(36);
}

export function formatContactName(contact: Contact): string {
  if (contact.ragione_sociale) return contact.ragione_sociale;
  const parts = [contact.name, contact.surname].filter(Boolean);
  return parts.length > 0 ? parts.join(" ") : "Contatto sconosciuto";
}

export function formatDate(date: Date): string {
  return new Intl.DateTimeFormat("it-IT", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

export function formatShortDate(date: Date): string {
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  const minutes = Math.floor(diff / 60_000);
  const hours = Math.floor(diff / 3_600_000);
  const days = Math.floor(diff / 86_400_000);

  if (minutes < 1) return "adesso";
  if (minutes < 60) return `${minutes}m fa`;
  if (hours < 24) return `${hours}h fa`;
  if (days === 1) return "ieri";
  return new Intl.DateTimeFormat("it-IT", { day: "2-digit", month: "2-digit" }).format(date);
}

export function sessionTitle(session: Session): string {
  const firstUserMessage = session.messages.find((m) => m.role === "user");
  if (firstUserMessage?.attachedFileName) {
    return firstUserMessage.attachedFileName;
  }
  if (firstUserMessage?.content) {
    return firstUserMessage.content.slice(0, 48) + (firstUserMessage.content.length > 48 ? "…" : "");
  }
  return "Nuova sessione";
}

export function confidenceLabel(score: number): string {
  const pct = Math.round(score * (score <= 1 ? 100 : 1));
  return `${pct}%`;
}

export function confidenceColorClass(score: number): string {
  const pct = score <= 1 ? score * 100 : score;
  if (pct >= 85) return "text-[var(--color-success)]";
  if (pct >= 70) return "text-[var(--color-warning)]";
  return "text-[var(--color-error)]";
}

export function createLoadingMessage(): Message {
  return {
    id: generateId(),
    role: "assistant",
    content: "",
    isLoading: true,
    timestamp: new Date(),
  };
}

export function deserializeSession(raw: unknown): Session | null {
  try {
    const s = raw as Session & { createdAt: string; updatedAt: string; messages: Array<Message & { timestamp: string }> };
    return {
      ...s,
      createdAt: new Date(s.createdAt),
      updatedAt: new Date(s.updatedAt),
      messages: s.messages.map((m) => ({ ...m, timestamp: new Date(m.timestamp) })),
    };
  } catch {
    return null;
  }
}

export function loadSessionsFromStorage(): Session[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = localStorage.getItem("documentai_sessions");
    if (!raw) return [];
    const parsed = JSON.parse(raw) as unknown[];
    return parsed.flatMap((s) => {
      const session = deserializeSession(s);
      return session ? [session] : [];
    });
  } catch {
    return [];
  }
}

export function saveSessionsToStorage(sessions: Session[]): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem("documentai_sessions", JSON.stringify(sessions));
  } catch {
    // storage quota exceeded or unavailable
  }
}
