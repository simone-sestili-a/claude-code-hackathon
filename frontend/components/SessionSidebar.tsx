"use client";

import React from "react";
import { Plus, MessageSquare, Trash2 } from "lucide-react";
import type { Session } from "@/lib/types";
import { formatShortDate, sessionTitle, cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";

interface SessionSidebarProps {
  sessions: Session[];
  activeId: string | null;
  onSelect: (id: string) => void;
  onNew: () => void;
  onDelete: (id: string) => void;
}

export function SessionSidebar({
  sessions,
  activeId,
  onSelect,
  onNew,
  onDelete,
}: SessionSidebarProps) {
  const sorted = [...sessions].sort(
    (a, b) => b.updatedAt.getTime() - a.updatedAt.getTime()
  );

  return (
    <aside
      className="flex flex-col h-full"
      style={{ background: "var(--color-sidebar)" }}
      aria-label="Sessioni"
    >
      {/* Logo + new button */}
      <div className="px-4 pt-5 pb-3">
        <div className="flex items-center justify-between mb-4">
          <div>
            <span className="text-sm font-semibold text-[var(--color-text)]">DocumentAI</span>
            <span className="block text-[0.65rem] font-medium uppercase tracking-widest text-[var(--color-accent)] mt-px">
              Ercole
            </span>
          </div>
          <Button
            variant="secondary"
            size="icon-sm"
            onClick={onNew}
            title="Nuova sessione"
            aria-label="Nuova sessione"
          >
            <Plus className="h-4 w-4" />
          </Button>
        </div>
        <Separator />
      </div>

      {/* Session list */}
      <nav className="flex-1 overflow-y-auto px-2 pb-4 space-y-0.5" aria-label="Elenco sessioni">
        {sorted.length === 0 && (
          <p className="px-3 pt-4 text-xs text-[var(--color-text-tertiary)] text-center leading-relaxed">
            Nessuna sessione.
            <br />
            Carica un documento per iniziare.
          </p>
        )}
        {sorted.map((session) => {
          const isActive = session.id === activeId;
          const title = sessionTitle(session);
          const messageCount = session.messages.filter((m) => !m.isLoading).length;

          return (
            <div key={session.id} className="group relative">
              <button
                onClick={() => onSelect(session.id)}
                className={cn(
                  "w-full flex items-start gap-2.5 rounded px-3 py-2.5 text-left transition-colors duration-150",
                  "focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[var(--color-accent)]",
                  isActive
                    ? "bg-[var(--color-sidebar-active)]"
                    : "hover:bg-[var(--color-sidebar-active)]"
                )}
                aria-current={isActive ? "page" : undefined}
              >
                <MessageSquare
                  className="h-3.5 w-3.5 mt-0.5 shrink-0 text-[var(--color-text-tertiary)]"
                  aria-hidden
                />
                <div className="flex-1 min-w-0">
                  <p
                    className={cn(
                      "text-xs truncate leading-snug",
                      isActive
                        ? "font-medium text-[var(--color-text)]"
                        : "text-[var(--color-text-secondary)]"
                    )}
                  >
                    {title}
                  </p>
                  <p className="text-[0.65rem] text-[var(--color-text-tertiary)] mt-0.5">
                    {formatShortDate(session.updatedAt)}
                    {messageCount > 0 && (
                      <span className="ml-2 opacity-70">
                        {messageCount} {messageCount === 1 ? "msg" : "msg"}
                      </span>
                    )}
                  </p>
                </div>
              </button>

              {/* Delete button — hover on desktop, always visible on mobile */}
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onDelete(session.id);
                }}
                className="absolute right-1 top-1/2 -translate-y-1/2 p-2 rounded opacity-100 sm:opacity-0 group-hover:opacity-100 transition-opacity duration-150 text-[var(--color-text-tertiary)] hover:text-[var(--color-error)] focus-visible:opacity-100 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[var(--color-accent)]"
                aria-label={`Elimina sessione "${title}"`}
                title="Elimina sessione"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            </div>
          );
        })}
      </nav>

      {/* Footer hint */}
      <div className="px-4 py-3 border-t border-[var(--color-border-subtle)]">
        <p className="text-[0.65rem] text-[var(--color-text-tertiary)] leading-relaxed">
          Le sessioni sono salvate localmente nel browser.
        </p>
      </div>
    </aside>
  );
}
