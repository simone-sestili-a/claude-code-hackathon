"use client";

import React, { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { ChevronDown, ChevronUp, FileText, AlertTriangle } from "lucide-react";
import type { DocumentProcessingResponse, Contact, ErcoleRequest } from "@/lib/types";
import {
  formatContactName,
  confidenceLabel,
  confidenceColorClass,
} from "@/lib/utils";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

// ---------------------------------------------------------------------------
// Contact display
// ---------------------------------------------------------------------------

function ContactRow({ label, value }: { label: string; value: string | undefined }) {
  if (!value) return null;
  return (
    <div className="flex gap-3 text-sm leading-snug py-0.5">
      <span className="w-36 shrink-0 text-[var(--color-text-tertiary)] text-xs uppercase tracking-wide font-medium pt-px">
        {label}
      </span>
      <span className="text-[var(--color-text)]">{value}</span>
    </div>
  );
}

function ContactBlock({ contact }: { contact: Contact }) {
  const name = formatContactName(contact);
  const isPf = !contact.ragione_sociale;

  return (
    <div className="py-2">
      <p className="text-sm font-medium text-[var(--color-text)] mb-1.5">{name}</p>
      <div className="space-y-0.5">
        {isPf ? (
          <>
            <ContactRow label="Codice fiscale" value={contact.fiscal_code} />
            <ContactRow
              label="Data nascita"
              value={
                contact.data_nascita
                  ? [contact.data_nascita, contact.luogo_nascita, contact.provincia_nascita && `(${contact.provincia_nascita})`]
                      .filter(Boolean)
                      .join(" · ")
                  : undefined
              }
            />
            <ContactRow label="Genere" value={contact.genere} />
          </>
        ) : (
          <>
            <ContactRow label="Ragione sociale" value={contact.ragione_sociale} />
            <ContactRow label="Partita IVA" value={contact.piva} />
          </>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Module request section
// ---------------------------------------------------------------------------

function ModuleSection({
  request,
  index,
  pages,
}: {
  request: ErcoleRequest;
  index: number;
  pages: number[];
}) {
  const [expanded, setExpanded] = useState(false);
  const confPct = request.confidence_score <= 1 ? request.confidence_score * 100 : request.confidence_score;
  const confClass = confidenceColorClass(request.confidence_score);

  return (
    <div className="py-5 animate-fade-in">
      {/* Header row */}
      <div className="flex items-start gap-3">
        <span
          className="text-xs font-mono font-semibold mt-0.5 w-5 shrink-0 text-right"
          style={{ color: "var(--color-text-tertiary)" }}
          aria-label={`Modulo ${index}`}
        >
          {index}
        </span>
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-4">
            <h3 className="text-sm font-semibold text-[var(--color-text)] leading-snug">
              {request.header}
            </h3>
            <span
              className={`text-xs font-medium tabular-nums shrink-0 ${confClass}`}
              title={`Confidenza: ${confidenceLabel(request.confidence_score)}`}
            >
              {confidenceLabel(request.confidence_score)}
            </span>
          </div>

          {/* Pages */}
          {pages.length > 0 && (
            <div className="mt-1.5 flex flex-wrap items-center gap-1.5">
              <span className="text-xs text-[var(--color-text-tertiary)]">
                {pages.length === 1 ? "Pagina" : "Pagine"}
              </span>
              {pages.map((p) => (
                <Badge key={p} variant="neutral" className="font-mono text-xs px-1.5 py-0">
                  {p}
                </Badge>
              ))}
            </div>
          )}

          {/* Contacts */}
          {request.contacts.length > 0 && (
            <div className="mt-3 space-y-1">
              {request.contacts.map((c, i) => (
                <ContactBlock key={i} contact={c} />
              ))}
            </div>
          )}

          {/* Notes */}
          {request.notes && (
            <p className="mt-2 text-xs text-[var(--color-text-secondary)] italic">
              {request.notes}
            </p>
          )}

          {/* Expandable: external modules + page reasoning */}
          {(request.external_modules.length > 0) && (
            <Button
              variant="ghost"
              size="sm"
              className="mt-2 h-7 px-0 text-xs text-[var(--color-text-tertiary)] hover:text-[var(--color-text)]"
              onClick={() => setExpanded((v) => !v)}
              aria-expanded={expanded}
            >
              {expanded ? (
                <><ChevronUp className="h-3 w-3 mr-1" /> Meno dettagli</>
              ) : (
                <><ChevronDown className="h-3 w-3 mr-1" /> Moduli esterni ({request.external_modules.length})</>
              )}
            </Button>
          )}

          {expanded && request.external_modules.length > 0 && (
            <div className="mt-2 space-y-1">
              {request.external_modules.map((em, i) => (
                <div key={i} className="flex items-center gap-2 text-xs text-[var(--color-text-secondary)]">
                  <FileText className="h-3 w-3 shrink-0 text-[var(--color-text-tertiary)]" />
                  <span>{em.module_name}</span>
                  {em.ercole_related && (
                    <Badge variant="default" className="text-[0.65rem] px-1 py-0">Ercole</Badge>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main DocumentResult component
// ---------------------------------------------------------------------------

interface DocumentResultProps {
  result: DocumentProcessingResponse;
}

export function DocumentResult({ result }: DocumentResultProps) {
  const [summaryExpanded, setSummaryExpanded] = useState(true);

  return (
    <div className="animate-slide-in">
      {/* Top-line stats */}
      <div className="flex items-center gap-5 mb-4 text-sm">
        <div className="flex items-center gap-1.5 text-[var(--color-text-secondary)]">
          <FileText className="h-4 w-4" />
          <span>
            <span className="font-semibold text-[var(--color-text)]">{result.total_pages}</span>{" "}
            {result.total_pages === 1 ? "pagina" : "pagine"}
          </span>
        </div>
        <div className="flex items-center gap-1.5 text-[var(--color-text-secondary)]">
          <span>
            <span className="font-semibold text-[var(--color-text)]">{result.requests.length}</span>{" "}
            {result.requests.length === 1 ? "modulo identificato" : "moduli identificati"}
          </span>
        </div>
        {result.external_modules.length > 0 && (
          <div className="flex items-center gap-1.5 text-[var(--color-warning)]">
            <AlertTriangle className="h-3.5 w-3.5" />
            <span className="text-xs">{result.external_modules.length} moduli non riconosciuti</span>
          </div>
        )}
      </div>

      {/* Summary */}
      {result.summary && (
        <div className="mb-5">
          <button
            className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-[var(--color-text-tertiary)] hover:text-[var(--color-text-secondary)] transition-colors duration-150 mb-2"
            onClick={() => setSummaryExpanded((v) => !v)}
            aria-expanded={summaryExpanded}
          >
            {summaryExpanded ? (
              <ChevronUp className="h-3 w-3" />
            ) : (
              <ChevronDown className="h-3 w-3" />
            )}
            Riepilogo
          </button>
          {summaryExpanded && (
            <div className="prose-document animate-fade-in">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {result.summary}
              </ReactMarkdown>
            </div>
          )}
        </div>
      )}

      {/* Module list */}
      {result.requests.length > 0 && (
        <>
          <Separator className="mb-1" />
          <div className="divide-y divide-[var(--color-border-subtle)]">
            {result.requests.map((req, i) => {
              const assignment = result.page_assignments[req.request_id];
              const pages = assignment?.pages ?? [];
              return (
                <ModuleSection
                  key={req.request_id}
                  request={req}
                  index={i + 1}
                  pages={pages}
                />
              );
            })}
          </div>
        </>
      )}

      {/* Unrecognized external modules */}
      {result.external_modules.length > 0 && (
        <div className="mt-4 p-3 rounded bg-[var(--color-warning-bg)]">
          <p className="text-xs font-semibold text-[var(--color-warning)] mb-2 flex items-center gap-1.5">
            <AlertTriangle className="h-3.5 w-3.5" /> Moduli non riconosciuti
          </p>
          <ul className="space-y-1">
            {result.external_modules.map((name, i) => (
              <li key={i} className="text-xs text-[var(--color-text-secondary)]">
                {name}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
