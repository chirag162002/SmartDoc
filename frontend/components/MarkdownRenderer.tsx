"use client";

import React from "react";
import { BookOpen, ChevronRight, Layers, Sparkles } from "lucide-react";
import { Citation } from "@/lib/api";

interface MarkdownRendererProps {
  content: string;
  citations?: Citation[];
  onCitationClick?: (citationTag: string) => void;
  className?: string;
}

/**
 * Pre-processes LLM text output by normalizing concatenated lists (e.g. "1. Title... - Point 1 2. Title...")
 * into structured markdown with explicit line breaks before numbered entries, bullets, and section headers.
 */
const preprocessContent = (raw: string): string => {
  if (!raw) return "";
  let text = raw;

  // 1. Unescape literal escaped backslash-n sequences ("\\n") into real newlines
  text = text.replace(/\\n/g, "\n");

  // 2. Safety unwrapper: If text is a raw JSON string starting with `{`
  if (
    text.trim().startsWith("{") &&
    (text.includes('"executive_summary"') || text.includes('"detailed_summary"'))
  ) {
    try {
      const parsed = JSON.parse(text);
      if (parsed.executive_summary || parsed.detailed_summary) {
        text = parsed.executive_summary || parsed.detailed_summary;
      }
    } catch {
      const matchExec = text.match(/"executive_summary"\s*:\s*"([\s\S]*?)"/);
      const matchDet = text.match(/"detailed_summary"\s*:\s*"([\s\S]*?)"/);
      if (matchExec || matchDet) {
        text = (matchExec ? matchExec[1] : "") || (matchDet ? matchDet[1] : "");
        text = text.replace(/\\n/g, "\n").replace(/\\"/g, '"');
      }
    }
  }

  // 3. Clean up redundant literal "(Page N)" or "(Page Ref)" right after citation tags [Ref: CHUNK-...]
  text = text.replace(
    /(\[Ref:\s*CHUNK-[A-Za-z0-9_\-]+\]|\[CHUNK-[A-Za-z0-9_\-]+\])\s*\(\s*Page\s*\d+\s*\)/gi,
    "$1"
  );

  // 4. Insert double newlines before inline list items and section headers
  text = text.replace(/([^\n])\s+(\d+\.\s+)/g, "$1\n\n$2");
  text = text.replace(/([^\n])\s+([-•*]\s+)/g, "$1\n$2");
  text = text.replace(/([^\n])\s+(#{1,4}\s+)/g, "$1\n\n$2");

  return text;
};

export const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({
  content,
  citations = [],
  onCitationClick,
  className = "",
}) => {
  if (!content) return null;

  const normalizedText = preprocessContent(content);
  const lines = normalizedText.split("\n");

  const renderInlineFormatting = (text: string) => {
    // Replace citation tags like [Ref: CHUNK-123-P1-C0] or [CHUNK-123-P1-C0] with interactive badges
    const citationRegex = /(\[Ref:\s*CHUNK-[A-Za-z0-9_\-]+\]|\[CHUNK-[A-Za-z0-9_\-]+\])/g;
    const parts = text.split(citationRegex);

    return parts.map((part, i) => {
      if (part.match(citationRegex)) {
        const cleanTag = part.replace(/^\[(Ref:\s*)?/, "").replace(/\]$/, "");

        // Extract page number if present (e.g., P1, P-1, Page-1, Page1)
        const pageMatch =
          cleanTag.match(/[-_]P(?:age)?[-_]?(\d+)/i) || cleanTag.match(/Page[-_]?(\d+)/i);
        const displayLabel = pageMatch ? `Page ${pageMatch[1]}` : "Source Ref";

        return (
          <button
            key={i}
            onClick={() => onCitationClick && onCitationClick(cleanTag)}
            data-chunk-id={cleanTag}
            className="inline-flex items-center gap-1 mx-1 px-2 py-0.5 rounded bg-indigo-500/15 hover:bg-indigo-500/30 text-indigo-700 dark:text-indigo-300 text-[11px] font-medium border border-indigo-500/30 transition-all shadow-sm active:scale-95 cursor-pointer"
            title={`Source Chunk ID: ${cleanTag} (Click to inspect source)`}
          >
            <BookOpen className="w-3 h-3 text-indigo-600 dark:text-indigo-400" />
            {displayLabel}
          </button>
        );
      }

      // Handle bold formatting **bold**
      const boldParts = part.split(/(\*\*.*?\*\*)/g);
      return boldParts.map((bPart, j) => {
        if (bPart.startsWith("**") && bPart.endsWith("**")) {
          return (
            <strong key={j} className="text-slate-900 dark:text-white font-semibold">
              {bPart.slice(2, -2)}
            </strong>
          );
        }
        return bPart;
      });
    });
  };

  const elements: React.ReactNode[] = [];
  let currentList: React.ReactNode[] = [];
  let currentListType: "numbered" | "bullet" | null = null;

  const flushList = (keySuffix: string | number) => {
    if (currentList.length > 0) {
      if (currentListType === "numbered") {
        elements.push(
          <div key={`numbered-group-${keySuffix}`} className="space-y-3 my-3">
            {currentList}
          </div>
        );
      } else {
        elements.push(
          <ul key={`bullet-group-${keySuffix}`} className="space-y-2 my-2.5 pl-1">
            {currentList}
          </ul>
        );
      }
      currentList = [];
      currentListType = null;
    }
  };

  lines.forEach((line, index) => {
    const trimmed = line.trim();
    if (!trimmed) {
      flushList(index);
      return;
    }

    // Check for Horizontal Divider Lines (e.g. ===... or ---... or ___...)
    if (trimmed.match(/^[=\-_]{3,}$/)) {
      flushList(index);
      elements.push(<hr key={index} className="my-3 border-slate-200 dark:border-slate-800" />);
      return;
    }

    // Check for Headers (### Header or ## Header)
    if (trimmed.match(/^#{1,4}\s+/)) {
      flushList(index);
      const cleanHeader = trimmed.replace(/^#{1,4}\s+/, "");
      elements.push(
        <div key={index} className="mt-5 mb-3">
          <h4 className="text-xs sm:text-sm font-bold text-slate-900 dark:text-white uppercase tracking-wider flex items-center gap-2 pb-1.5 border-b border-indigo-500/30">
            <Sparkles className="w-3.5 h-3.5 text-indigo-600 dark:text-indigo-400" />
            {renderInlineFormatting(cleanHeader)}
          </h4>
        </div>
      );
      return;
    }

    // Check for Numbered List Items (1. Item)
    const numberedMatch = trimmed.match(/^(\d+)\.\s+(.*)/);
    if (numberedMatch) {
      if (currentListType === "bullet") {
        flushList(`num-switch-${index}`);
      }
      currentListType = "numbered";

      currentList.push(
        <div
          key={index}
          className="p-3.5 rounded-xl bg-white dark:bg-slate-900/80 border border-slate-200 dark:border-slate-800/90 shadow-md space-y-2 transition-all hover:border-indigo-400 dark:hover:border-slate-700/80"
        >
          <div className="flex items-start gap-2.5">
            <span className="flex-shrink-0 w-5 h-5 rounded-md bg-indigo-500/10 dark:bg-indigo-500/20 text-indigo-700 dark:text-indigo-300 font-mono text-[11px] font-bold flex items-center justify-center border border-indigo-500/30 mt-0.5">
              {numberedMatch[1]}
            </span>
            <div className="flex-1 text-slate-800 dark:text-slate-100 font-medium leading-relaxed">
              {renderInlineFormatting(numberedMatch[2])}
            </div>
          </div>
        </div>
      );
      return;
    }

    // Check for Bullet Points (- Item or • Item)
    const bulletMatch = trimmed.match(/^[-•*]\s+(.*)/);
    if (bulletMatch) {
      if (currentListType === "numbered") {
        // If bullet follows a numbered item, render it as indented sub-bullet inside the list
        currentList.push(
          <div
            key={`sub-bullet-${index}`}
            className="ml-7 pl-3 border-l border-indigo-500/30 my-1 text-xs text-slate-700 dark:text-slate-300 flex items-start gap-2"
          >
            <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 dark:bg-emerald-400 mt-1.5 flex-shrink-0" />
            <div className="flex-1 leading-relaxed">{renderInlineFormatting(bulletMatch[1])}</div>
          </div>
        );
        return;
      }

      currentListType = "bullet";
      currentList.push(
        <li
          key={index}
          className="flex items-start gap-2.5 text-slate-800 dark:text-slate-200 text-xs sm:text-sm"
        >
          <div className="w-1.5 h-1.5 rounded-full bg-indigo-600 dark:bg-indigo-400 mt-2 flex-shrink-0" />
          <span className="flex-1 leading-relaxed">{renderInlineFormatting(bulletMatch[1])}</span>
        </li>
      );
      return;
    }

    // Standard Paragraph
    flushList(index);
    elements.push(
      <p
        key={index}
        className="leading-relaxed text-slate-800 dark:text-slate-300 text-xs sm:text-sm mb-2.5"
      >
        {renderInlineFormatting(trimmed)}
      </p>
    );
  });

  flushList("end");

  return <div className={`space-y-1 ${className}`}>{elements}</div>;
};
