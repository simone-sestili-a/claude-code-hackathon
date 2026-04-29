"use client";

import React, { useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { Upload, FileText, X } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

interface PdfDropzoneProps {
  file: File | null;
  onFile: (file: File | null) => void;
  disabled?: boolean;
  compact?: boolean;
}

export function PdfDropzone({ file, onFile, disabled, compact }: PdfDropzoneProps) {
  const onDrop = useCallback(
    (accepted: File[]) => {
      if (accepted[0]) onFile(accepted[0]);
    },
    [onFile]
  );

  const { getRootProps, getInputProps, isDragActive, open } = useDropzone({
    onDrop,
    accept: { "application/pdf": [".pdf"] },
    maxFiles: 1,
    disabled,
    noClick: !!file,
    noKeyboard: !!file,
  });

  // Compact mode: just the file chip + remove button (used inside input area)
  if (compact && file) {
    return (
      <div className="flex items-center gap-1.5 rounded bg-[var(--color-accent-subtle)] px-2 py-1 text-xs text-[var(--color-accent)]">
        <FileText className="h-3.5 w-3.5 shrink-0" />
        <span className="max-w-32 truncate font-medium">{file.name}</span>
        <button
          type="button"
          onClick={() => onFile(null)}
          className="ml-0.5 text-[var(--color-accent)] hover:opacity-70 transition-opacity duration-150"
          aria-label="Rimuovi PDF"
          disabled={disabled}
        >
          <X className="h-3 w-3" />
        </button>
      </div>
    );
  }

  // Full dropzone
  return (
    <div
      {...getRootProps()}
      className={cn(
        "relative flex flex-col items-center justify-center gap-3 rounded-md border-2 border-dashed p-8 text-center transition-colors duration-150",
        isDragActive
          ? "border-[var(--color-accent)] bg-[var(--color-accent-muted)]"
          : "border-[var(--color-border)] bg-[var(--color-surface)] hover:border-[var(--color-accent)] hover:bg-[var(--color-accent-muted)]",
        disabled && "opacity-50 pointer-events-none",
        file && "border-[var(--color-accent)] bg-[var(--color-accent-muted)]"
      )}
    >
      <input {...getInputProps()} aria-label="Carica PDF" />

      {file ? (
        <>
          <div className="flex h-10 w-10 items-center justify-center rounded bg-[var(--color-accent-subtle)]">
            <FileText className="h-5 w-5 text-[var(--color-accent)]" />
          </div>
          <div>
            <p className="text-sm font-medium text-[var(--color-text)]">{file.name}</p>
            <p className="text-xs text-[var(--color-text-tertiary)] mt-0.5">
              {(file.size / 1024).toFixed(0)} KB
            </p>
          </div>
          <Button
            type="button"
            variant="secondary"
            size="sm"
            onClick={(e) => {
              e.stopPropagation();
              onFile(null);
            }}
          >
            <X className="h-3.5 w-3.5 mr-1" />
            Rimuovi
          </Button>
        </>
      ) : (
        <>
          <div className="flex h-10 w-10 items-center justify-center rounded bg-[var(--color-sidebar)]">
            <Upload
              className={cn(
                "h-5 w-5 transition-colors duration-150",
                isDragActive ? "text-[var(--color-accent)]" : "text-[var(--color-text-tertiary)]"
              )}
            />
          </div>
          <div>
            <p className="text-sm font-medium text-[var(--color-text)]">
              {isDragActive ? "Rilascia il file PDF" : "Trascina un PDF qui"}
            </p>
            <p className="text-xs text-[var(--color-text-tertiary)] mt-1">
              o{" "}
              <button
                type="button"
                onClick={open}
                className="text-[var(--color-accent)] hover:underline underline-offset-2 focus-visible:outline-none"
              >
                sfoglia i file
              </button>
            </p>
          </div>
        </>
      )}
    </div>
  );
}
