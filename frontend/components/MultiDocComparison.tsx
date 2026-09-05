"use client";

import React, { useState, useEffect } from "react";
import {
  Layers,
  FileText,
  CheckCircle2,
  AlertTriangle,
  Sparkles,
  ArrowRight,
  Loader2,
} from "lucide-react";
import { DocumentItem, ComparisonResponse, fetchDocuments, compareDocuments } from "@/lib/api";

export const MultiDocComparison: React.FC = () => {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [selectedDocIds, setSelectedDocIds] = useState<string[]>([]);
  const [comparison, setComparison] = useState<ComparisonResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isFetchingDocs, setIsFetchingDocs] = useState<boolean>(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    const loadDocs = async () => {
      try {
        const list = await fetchDocuments();
        const completed = list.filter((d) => d.status === "COMPLETE");
        setDocuments(completed);
        if (completed.length >= 2) {
          setSelectedDocIds([completed[0].id, completed[1].id]);
        }
      } catch (err: unknown) {
        console.error("Failed to load documents:", err);
      } finally {
        setIsFetchingDocs(false);
      }
    };
    loadDocs();
  }, []);

  const toggleDocSelection = (id: string) => {
    setSelectedDocIds((prev) => (prev.includes(id) ? prev.filter((d) => d !== id) : [...prev, id]));
  };

  const handleRunComparison = async () => {
    if (selectedDocIds.length < 2) return;
    setIsLoading(true);
    setErrorMsg(null);
    try {
      const result = await compareDocuments(selectedDocIds);
      setComparison(result);
    } catch (err: unknown) {
      setErrorMsg((err as Error).message || "Failed to compare documents.");
    } finally {
      setIsLoading(false);
    }
  };

  if (isFetchingDocs) {
    return (
      <div className="w-full glass-panel p-12 rounded-2xl border border-slate-800 text-center text-slate-400">
        <Loader2 className="w-6 h-6 animate-spin mx-auto mb-2 text-indigo-400" />
        Loading completed documents...
      </div>
    );
  }

  return (
    <div className="w-full max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-200 dark:border-slate-800 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 transition-colors">
        <div>
          <h2 className="text-xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <Layers className="w-6 h-6 text-indigo-600 dark:text-indigo-400" />
            Multi-Document Comparison Workspace
          </h2>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Select 2 or more documents to generate a cross-document comparative analysis matrix.
          </p>
        </div>

        <button
          onClick={handleRunComparison}
          disabled={selectedDocIds.length < 2 || isLoading}
          className="px-6 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-medium text-sm shadow-lg shadow-indigo-600/30 transition-all flex items-center gap-2 cursor-pointer"
        >
          {isLoading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Synthesizing...
            </>
          ) : (
            <>
              <Sparkles className="w-4 h-4" />
              Compare ({selectedDocIds.length}) Docs
            </>
          )}
        </button>
      </div>

      {/* Document Selection Grid */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-200 dark:border-slate-800 space-y-4 transition-colors">
        <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-300">
          Select Documents to Compare:
        </h3>

        {documents.length === 0 ? (
          <p className="text-sm text-slate-500 dark:text-slate-400 italic">
            No completed documents available in your library. Upload documents first!
          </p>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {documents.map((doc) => {
              const isSelected = selectedDocIds.includes(doc.id);
              return (
                <div
                  key={doc.id}
                  onClick={() => toggleDocSelection(doc.id)}
                  className={`p-4 rounded-xl border cursor-pointer transition-all flex items-center justify-between ${
                    isSelected
                      ? "bg-indigo-500/10 dark:bg-indigo-600/20 border-indigo-500 text-slate-900 dark:text-white shadow-md shadow-indigo-500/10"
                      : "bg-slate-100/80 dark:bg-slate-900/60 border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-400 hover:border-slate-300 dark:hover:border-slate-700 hover:text-slate-900 dark:hover:text-slate-200"
                  }`}
                >
                  <div className="flex items-center gap-3 overflow-hidden">
                    <FileText
                      className={`w-5 h-5 flex-shrink-0 ${isSelected ? "text-indigo-600 dark:text-indigo-400" : "text-slate-400 dark:text-slate-500"}`}
                    />
                    <div className="truncate">
                      <p className="text-sm font-semibold truncate">{doc.original_name}</p>
                      <p className="text-[11px] text-slate-500 dark:text-slate-400 uppercase">
                        {doc.file_type} • {doc.page_count} page(s)
                      </p>
                    </div>
                  </div>
                  <div
                    className={`w-5 h-5 rounded-full border flex items-center justify-center ${isSelected ? "border-indigo-500 bg-indigo-600 text-white" : "border-slate-300 dark:border-slate-700"}`}
                  >
                    {isSelected && <CheckCircle2 className="w-3.5 h-3.5" />}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Error Alert */}
      {errorMsg && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-600 dark:text-rose-400 text-sm flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 flex-shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Comparison Matrix Results */}
      {comparison && (
        <div className="space-y-6">
          {/* Comparative Summary Card */}
          <div className="glass-panel p-6 rounded-2xl border border-indigo-500/30 space-y-3 bg-gradient-to-br from-slate-100 via-indigo-50/50 to-slate-100 dark:from-slate-900/90 dark:via-indigo-950/20 dark:to-slate-900/90">
            <h3 className="text-base font-semibold text-indigo-700 dark:text-indigo-300 flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
              Cross-Document Synthesis
            </h3>
            <p className="text-sm text-slate-800 dark:text-slate-200 leading-relaxed bg-white/80 dark:bg-slate-950/60 p-4 rounded-xl border border-indigo-500/20">
              {comparison.comparative_summary}
            </p>
          </div>

          {/* Side-by-Side Matrix Table */}
          <div className="glass-panel p-6 rounded-2xl border border-slate-200 dark:border-slate-800 space-y-4 transition-colors">
            <h3 className="text-base font-semibold text-slate-900 dark:text-white">
              Side-by-Side Document Matrix
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {comparison.matrix.map((item) => (
                <div
                  key={item.document_id}
                  className="glass-panel p-5 rounded-xl border border-slate-200 dark:border-slate-800 space-y-4 bg-slate-100/90 dark:bg-slate-900/60 transition-colors"
                >
                  <div className="border-b border-slate-200 dark:border-slate-800 pb-3">
                    <h4 className="text-sm font-bold text-slate-900 dark:text-white truncate">
                      {item.filename}
                    </h4>
                    <span className="text-[10px] px-2 py-0.5 bg-indigo-500/10 dark:bg-indigo-500/20 text-indigo-700 dark:text-indigo-300 rounded uppercase font-semibold">
                      {item.file_type}
                    </span>
                  </div>

                  <div>
                    <h5 className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase mb-1">
                      Executive Summary
                    </h5>
                    <p className="text-xs text-slate-700 dark:text-slate-300 line-clamp-4 leading-relaxed">
                      {item.executive_summary}
                    </p>
                  </div>

                  {item.key_metrics.length > 0 && (
                    <div>
                      <h5 className="text-xs font-semibold text-emerald-600 dark:text-emerald-400 uppercase mb-1">
                        Key Metrics
                      </h5>
                      <ul className="text-xs text-slate-700 dark:text-slate-300 space-y-1 font-mono">
                        {item.key_metrics.map((m, i) => (
                          <li
                            key={i}
                            className="bg-white dark:bg-slate-950 p-1.5 rounded border border-slate-200 dark:border-slate-800/60"
                          >
                            • {m}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {item.top_risks.length > 0 && (
                    <div>
                      <h5 className="text-xs font-semibold text-amber-600 dark:text-amber-400 uppercase mb-1">
                        Top Risks
                      </h5>
                      <ul className="text-xs text-slate-700 dark:text-slate-300 space-y-1">
                        {item.top_risks.map((r, i) => (
                          <li
                            key={i}
                            className="bg-rose-500/10 text-rose-700 dark:text-rose-300 p-1.5 rounded border border-rose-500/20"
                          >
                            ⚠️ {r}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
