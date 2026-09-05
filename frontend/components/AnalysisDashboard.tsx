"use client";

import React, { useState, useEffect } from "react";
import {
  FileText,
  Sparkles,
  AlertTriangle,
  CheckSquare,
  BarChart3,
  Hash,
  Tag,
  MessageSquare,
  ChevronRight,
  ShieldAlert,
  Calendar,
  Layers,
  ArrowLeft,
  Info,
} from "lucide-react";
import { DocumentItem, DocumentAnalysis, fetchDocumentAnalysis } from "@/lib/api";
import { GroundedChat } from "@/components/GroundedChat";
import { MarkdownRenderer } from "@/components/MarkdownRenderer";

interface AnalysisDashboardProps {
  document: DocumentItem;
  onBack: () => void;
}

export const AnalysisDashboard: React.FC<AnalysisDashboardProps> = ({ document, onBack }) => {
  const [analysis, setAnalysis] = useState<DocumentAnalysis | null>(null);
  const [activeTab, setActiveTab] = useState<"summary" | "detailed" | "tabular" | "risks">(
    "summary"
  );
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    const loadAnalysis = async () => {
      setIsLoading(true);
      try {
        const data = await fetchDocumentAnalysis(document.id);
        setAnalysis(data);
        if (data.tabular_metrics && Object.keys(data.tabular_metrics).length > 0) {
          setActiveTab("tabular");
        }
      } catch (err: unknown) {
        setErrorMsg((err as Error).message || "Failed to load analysis results.");
      } finally {
        setIsLoading(false);
      }
    };

    loadAnalysis();
  }, [document.id]);

  if (isLoading) {
    return (
      <div className="w-full glass-panel p-12 rounded-2xl border border-slate-800 text-center space-y-4">
        <div className="w-12 h-12 rounded-full bg-indigo-500/20 border border-indigo-500/30 flex items-center justify-center mx-auto text-indigo-400 animate-pulse">
          <Sparkles className="w-6 h-6" />
        </div>
        <h3 className="text-lg font-semibold text-white">Loading Document Intelligence...</h3>
      </div>
    );
  }

  if (errorMsg || !analysis) {
    return (
      <div className="w-full glass-panel p-8 rounded-2xl border border-rose-500/30 text-center space-y-4">
        <AlertTriangle className="w-10 h-10 text-rose-400 mx-auto" />
        <h3 className="text-lg font-semibold text-white">Analysis Unavailable</h3>
        <p className="text-sm text-slate-400">
          {errorMsg || "Could not retrieve analysis payload."}
        </p>
        <button
          onClick={onBack}
          className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-white text-sm"
        >
          Return to Dashboard
        </button>
      </div>
    );
  }

  const isTabular = Object.keys(analysis.tabular_metrics || {}).length > 0;

  return (
    <div className="w-full space-y-6">
      {/* Header Bar */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-200 dark:border-slate-800 flex flex-col md:flex-row items-start md:items-center justify-between gap-4 transition-colors">
        <div className="flex items-center gap-4">
          <button
            onClick={onBack}
            className="p-2.5 rounded-xl bg-slate-100 dark:bg-slate-900/80 hover:bg-slate-200 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white border border-slate-200 dark:border-slate-800 transition-all cursor-pointer"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-xl font-bold text-slate-900 dark:text-white">
                {document.original_name}
              </h2>
              <span className="px-2.5 py-0.5 rounded-full bg-indigo-500/10 dark:bg-indigo-500/20 text-indigo-700 dark:text-indigo-300 text-xs font-semibold uppercase border border-indigo-500/30">
                {document.file_type}
              </span>
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
              {document.page_count} page(s) / sheet(s) • Analysis complete
            </p>
          </div>
        </div>
      </div>

      {/* Fallback Banner */}
      {analysis.is_fallback && (
        <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-700 dark:text-amber-300 text-sm flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 flex-shrink-0 text-amber-500 dark:text-amber-400 mt-0.5" />
          <div>
            <p className="font-semibold text-amber-900 dark:text-amber-200">
              AI Summary Basic Mode Active
            </p>
            <p className="text-xs text-amber-800 dark:text-amber-300/90 mt-0.5">
              {analysis.fallback_notice ||
                "AI summary unavailable — showing extracted key sentences."}
            </p>
          </div>
        </div>
      )}

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Analysis Views */}
        <div className="lg:col-span-2 space-y-6">
          {/* Navigation Bar */}
          <div className="flex items-center gap-2 bg-slate-100 dark:bg-slate-900/80 p-1.5 rounded-xl border border-slate-200 dark:border-slate-800 overflow-x-auto transition-colors">
            <button
              onClick={() => setActiveTab("summary")}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all cursor-pointer ${
                activeTab === "summary"
                  ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/30"
                  : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-200/60 dark:hover:bg-slate-800/60"
              }`}
            >
              <Sparkles className="w-4 h-4" />
              Executive Summary
            </button>

            <button
              onClick={() => setActiveTab("detailed")}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all cursor-pointer ${
                activeTab === "detailed"
                  ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/30"
                  : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-200/60 dark:hover:bg-slate-800/60"
              }`}
            >
              <FileText className="w-4 h-4" />
              Detailed Breakdown
            </button>

            {isTabular && (
              <button
                onClick={() => setActiveTab("tabular")}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all cursor-pointer ${
                  activeTab === "tabular"
                    ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/30"
                    : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-200/60 dark:hover:bg-slate-800/60"
                }`}
              >
                <BarChart3 className="w-4 h-4" />
                Data & Table Insights
              </button>
            )}

            <button
              onClick={() => setActiveTab("risks")}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all cursor-pointer ${
                activeTab === "risks"
                  ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/30"
                  : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-200/60 dark:hover:bg-slate-800/60"
              }`}
            >
              <ShieldAlert className="w-4 h-4" />
              Risk Flags & Actions
            </button>
          </div>

          {/* Tab Content 1: Executive Summary */}
          {activeTab === "summary" && (
            <div className="glass-panel p-6 rounded-2xl border border-slate-200 dark:border-slate-800 space-y-6 transition-colors">
              <div>
                <h3 className="text-lg font-semibold text-slate-900 dark:text-white flex items-center gap-2 mb-3">
                  <Sparkles className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
                  Executive Summary
                </h3>
                <div className="bg-slate-100/90 dark:bg-slate-900/60 p-5 rounded-xl border border-slate-200 dark:border-slate-800/80 text-sm text-slate-800 dark:text-slate-200 transition-colors">
                  <MarkdownRenderer content={analysis.executive_summary} />
                </div>
              </div>

              {/* Key Numbers & Dates Grid */}
              {analysis.key_numbers_dates && analysis.key_numbers_dates.length > 0 && (
                <div>
                  <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-3 flex items-center gap-2">
                    <Hash className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
                    Key Numbers & Dates
                  </h4>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {analysis.key_numbers_dates.map((item, idx) => (
                      <div
                        key={idx}
                        className="p-3.5 rounded-xl bg-slate-100/90 dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800/80 flex items-center justify-between shadow-sm transition-colors"
                      >
                        <div>
                          <p className="text-xs text-slate-500 dark:text-slate-400 font-medium">
                            {item.label}
                          </p>
                          <p className="text-base font-bold text-emerald-600 dark:text-emerald-400 font-mono mt-0.5">
                            {item.value}
                          </p>
                        </div>
                        {item.citation && (
                          <span className="text-[10px] px-2 py-0.5 bg-indigo-500/10 dark:bg-indigo-500/20 text-indigo-700 dark:text-indigo-300 rounded border border-indigo-500/30 font-mono">
                            {item.citation}
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Topics & Entities Badges */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2 flex items-center gap-2">
                    <Tag className="w-4 h-4 text-indigo-400" />
                    Detected Topics
                  </h4>
                  <div className="flex flex-wrap gap-2">
                    {analysis.topics.map((topic, i) => (
                      <span
                        key={i}
                        className="px-3 py-1 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-xs font-medium"
                      >
                        {topic}
                      </span>
                    ))}
                  </div>
                </div>

                <div>
                  <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2 flex items-center gap-2">
                    <Layers className="w-4 h-4 text-purple-600 dark:text-purple-400" />
                    Key Entities
                  </h4>
                  <div className="flex flex-wrap gap-2">
                    {analysis.entities.map((entity, i) => (
                      <span
                        key={i}
                        className="px-3 py-1 rounded-lg bg-purple-500/10 border border-purple-500/20 text-purple-700 dark:text-purple-300 text-xs font-medium"
                      >
                        {entity.value} ({entity.category})
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Tab Content 2: Detailed Section Breakdown */}
          {activeTab === "detailed" && (
            <div className="glass-panel p-6 rounded-2xl border border-slate-200 dark:border-slate-800 transition-colors">
              <h3 className="text-lg font-semibold text-slate-900 dark:text-white flex items-center gap-2 mb-4">
                <FileText className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
                Detailed Section-by-Section Analysis
              </h3>
              <div className="bg-slate-100/90 dark:bg-slate-900/60 p-6 rounded-xl border border-slate-200 dark:border-slate-800 text-sm text-slate-800 dark:text-slate-200 transition-colors">
                <MarkdownRenderer content={analysis.detailed_summary} />
              </div>
            </div>
          )}

          {/* Tab Content 3: Tabular Statistics */}
          {activeTab === "tabular" && isTabular && (
            <div className="glass-panel p-6 rounded-2xl border border-slate-200 dark:border-slate-800 space-y-6 transition-colors">
              <h3 className="text-lg font-semibold text-slate-900 dark:text-white flex items-center gap-2">
                <BarChart3 className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
                Spreadsheet Tabular Profiling
              </h3>

              {Object.entries(analysis.tabular_metrics || {}).map(([sheetName, sheetData]) => (
                <div
                  key={sheetName}
                  className="space-y-4 bg-slate-100/90 dark:bg-slate-900/60 p-5 rounded-xl border border-slate-200 dark:border-slate-800"
                >
                  <div className="flex items-center justify-between">
                    <h4 className="text-base font-semibold text-slate-900 dark:text-white">
                      Sheet: {sheetName}
                    </h4>
                    <span className="text-xs px-2.5 py-1 bg-emerald-500/20 text-emerald-700 dark:text-emerald-300 rounded-full font-mono border border-emerald-500/30">
                      {((sheetData as Record<string, unknown>).rows_count as number | undefined) ||
                        ((sheetData as Record<string, unknown>).row_count as
                          number | undefined)}{" "}
                      rows ×{" "}
                      {((sheetData as Record<string, unknown>).columns_count as
                        number | undefined) ||
                        ((sheetData as Record<string, unknown>).col_count as
                          number | undefined)}{" "}
                      cols
                    </span>
                  </div>

                  {Boolean((sheetData as Record<string, unknown>).numeric_stats) &&
                    Object.keys(
                      (sheetData as Record<string, unknown>).numeric_stats as Record<
                        string,
                        unknown
                      >
                    ).length > 0 && (
                      <div className="overflow-x-auto">
                        <table className="w-full text-left text-xs border-collapse">
                          <thead>
                            <tr className="border-b border-slate-200 dark:border-slate-800 text-slate-500 dark:text-slate-400">
                              <th className="py-2 px-3">Column</th>
                              <th className="py-2 px-3">Min</th>
                              <th className="py-2 px-3">Max</th>
                              <th className="py-2 px-3">Mean</th>
                              <th className="py-2 px-3">Median</th>
                            </tr>
                          </thead>
                          <tbody>
                            {Object.entries(
                              (sheetData as Record<string, Record<string, unknown>>)
                                .numeric_stats || {}
                            ).map(([colName, colStats]) => (
                              <tr
                                key={colName}
                                className="border-b border-slate-200 dark:border-slate-800/40 text-slate-700 dark:text-slate-300 font-mono"
                              >
                                <td className="py-2 px-3 font-medium text-slate-900 dark:text-white">
                                  {colName}
                                </td>
                                <td className="py-2 px-3 text-slate-500 dark:text-slate-400 font-mono">
                                  {String((colStats as Record<string, unknown>).min ?? "-")}
                                </td>
                                <td className="py-2 px-3 text-slate-500 dark:text-slate-400 font-mono">
                                  {String((colStats as Record<string, unknown>).max ?? "-")}
                                </td>
                                <td className="py-2 px-3 text-emerald-600 dark:text-emerald-400 font-semibold font-mono">
                                  {String((colStats as Record<string, unknown>).mean ?? "-")}
                                </td>
                                <td className="py-2 px-3 text-indigo-600 dark:text-indigo-400 font-mono">
                                  {String((colStats as Record<string, unknown>).median ?? "-")}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                </div>
              ))}
            </div>
          )}

          {/* Tab Content 4: Risk Flags & Action Items */}
          {activeTab === "risks" && (
            <div className="glass-panel p-6 rounded-2xl border border-slate-200 dark:border-slate-800 space-y-6 transition-colors">
              <div>
                <h3 className="text-lg font-semibold text-slate-900 dark:text-white flex items-center gap-2 mb-4">
                  <ShieldAlert className="w-5 h-5 text-amber-500 dark:text-amber-400" />
                  Flagged Risks & Liabilities
                </h3>
                <div className="space-y-3">
                  {analysis.risk_flags && analysis.risk_flags.length > 0 ? (
                    analysis.risk_flags.map((risk, i) => (
                      <div
                        key={i}
                        className="p-4 rounded-xl bg-slate-100/90 dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800 flex items-start justify-between gap-4"
                      >
                        <div className="space-y-1">
                          <div className="flex items-center gap-2">
                            <span
                              className={`px-2 py-0.5 text-[10px] font-bold rounded uppercase ${
                                risk.severity === "HIGH"
                                  ? "bg-rose-500/20 text-rose-600 dark:text-rose-400 border border-rose-500/30"
                                  : risk.severity === "MEDIUM"
                                    ? "bg-amber-500/20 text-amber-600 dark:text-amber-400 border border-amber-500/30"
                                    : "bg-indigo-500/20 text-indigo-700 dark:text-indigo-300 border border-indigo-500/30"
                              }`}
                            >
                              {risk.severity || "MEDIUM"} Severity
                            </span>
                            <p className="text-sm font-semibold text-slate-900 dark:text-white">
                              {risk.risk}
                            </p>
                          </div>
                          {risk.description && (
                            <p className="text-xs text-slate-600 dark:text-slate-400">
                              {risk.description}
                            </p>
                          )}
                        </div>
                        {risk.citation && (
                          <span className="text-[10px] px-2 py-0.5 bg-slate-200 dark:bg-slate-800 text-slate-700 dark:text-slate-300 rounded font-mono">
                            {risk.citation}
                          </span>
                        )}
                      </div>
                    ))
                  ) : (
                    <p className="text-sm text-slate-500 dark:text-slate-400">
                      No critical risk flags detected.
                    </p>
                  )}
                </div>
              </div>

              <div>
                <h3 className="text-lg font-semibold text-slate-900 dark:text-white flex items-center gap-2 mb-4">
                  <CheckSquare className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
                  Identified Action Items
                </h3>
                <div className="space-y-3">
                  {analysis.action_items && analysis.action_items.length > 0 ? (
                    analysis.action_items.map((item, i) => (
                      <div
                        key={i}
                        className="p-4 rounded-xl bg-slate-100/90 dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800 flex items-center justify-between"
                      >
                        <div className="flex items-center gap-3">
                          <CheckSquare className="w-4 h-4 text-emerald-600 dark:text-emerald-400 flex-shrink-0" />
                          <span className="text-sm text-slate-800 dark:text-slate-200">
                            {item.item}
                          </span>
                        </div>
                        {item.owner && (
                          <span className="text-xs px-2.5 py-1 bg-slate-200 dark:bg-slate-800 text-slate-600 dark:text-slate-400 rounded-lg">
                            Owner: {item.owner}
                          </span>
                        )}
                      </div>
                    ))
                  ) : (
                    <p className="text-sm text-slate-500 dark:text-slate-400">
                      No explicit action items identified.
                    </p>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Right Column: Grounded AI Chat Sidebar */}
        <div className="lg:col-span-1">
          <GroundedChat documentIds={[document.id]} documentTitle={document.original_name} />
        </div>
      </div>
    </div>
  );
};
