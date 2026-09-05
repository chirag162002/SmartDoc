"use client";

import React, { useEffect, useState } from "react";
import { Sparkles, FileText, Layers, ShieldCheck, ShieldAlert, Cpu, RefreshCw } from "lucide-react";
import { fetchSystemStatus, SystemStatus } from "@/lib/api";

import { ThemeToggle } from "@/components/ThemeToggle";

interface NavbarProps {
  activeTab: "dashboard" | "library" | "compare";
  setActiveTab: (tab: "dashboard" | "library" | "compare") => void;
  documentCount: number;
}

export const Navbar: React.FC<NavbarProps> = ({ activeTab, setActiveTab, documentCount }) => {
  const [sysStatus, setSysStatus] = useState<SystemStatus | null>(null);

  const loadStatus = async () => {
    try {
      const data = await fetchSystemStatus();
      setSysStatus(data);
    } catch (err) {
      setSysStatus({
        status: "offline",
        provider: "ollama",
        model: "unknown",
        is_online: false,
        error_detail: "Backend API offline",
      });
    }
  };

  useEffect(() => {
    loadStatus();
    const interval = setInterval(loadStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="sticky top-0 z-50 glass-panel border-b border-slate-200/80 dark:border-slate-800/80 px-6 py-4 mb-8 bg-white/80 dark:bg-slate-900/80 backdrop-blur-xl transition-colors">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        {/* Brand Logo */}
        <div
          className="flex items-center gap-3 cursor-pointer"
          onClick={() => setActiveTab("dashboard")}
        >
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-emerald-400 flex items-center justify-center shadow-lg shadow-indigo-500/20">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold bg-gradient-to-r from-slate-900 via-indigo-900 to-indigo-600 dark:from-white dark:via-slate-200 dark:to-indigo-300 bg-clip-text text-transparent">
              SmartDoc
            </h1>
            <p className="text-xs text-slate-500 dark:text-slate-400 font-medium flex items-center gap-1">
              <Cpu className="w-3 h-3 text-indigo-500 dark:text-indigo-400" /> Multi-Format AI
              Intelligence
            </p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="flex items-center gap-2 bg-slate-100 dark:bg-slate-900/80 p-1.5 rounded-xl border border-slate-200 dark:border-slate-800 transition-colors">
          <button
            onClick={() => setActiveTab("dashboard")}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              activeTab === "dashboard"
                ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/30"
                : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-200/60 dark:hover:bg-slate-800/60"
            }`}
          >
            <Sparkles className="w-4 h-4" />
            Upload & Workspace
          </button>

          <button
            onClick={() => setActiveTab("library")}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              activeTab === "library"
                ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/30"
                : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-200/60 dark:hover:bg-slate-800/60"
            }`}
          >
            <FileText className="w-4 h-4" />
            Library
            {documentCount > 0 && (
              <span className="ml-1.5 px-2 py-0.5 text-xs bg-indigo-500/20 dark:bg-indigo-500/30 text-indigo-700 dark:text-indigo-300 rounded-full border border-indigo-500/30 font-semibold">
                {documentCount}
              </span>
            )}
          </button>

          <button
            onClick={() => setActiveTab("compare")}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              activeTab === "compare"
                ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/30"
                : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-200/60 dark:hover:bg-slate-800/60"
            }`}
          >
            <Layers className="w-4 h-4" />
            Compare Docs
          </button>
        </nav>

        {/* Right Section: Engine Status & Theme Toggle */}
        <div className="flex items-center gap-3">
          <ThemeToggle />

          <div className="hidden sm:flex items-center gap-2">
            {sysStatus?.is_online ? (
              <div
                className="flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-600 dark:text-emerald-400 text-xs font-semibold shadow-sm cursor-help"
                title={`Technical Details:\nLLM Provider: ${sysStatus.provider.toUpperCase()}\nModel: ${sysStatus.model}\nStatus: Active & Online`}
              >
                <ShieldCheck className="w-4 h-4 text-emerald-500 dark:text-emerald-400" />
                <span>
                  AI Engine: {sysStatus.provider === "ollama" ? "Local (Private)" : "Cloud"}
                </span>
              </div>
            ) : (
              <div
                className="flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-rose-500/10 border border-rose-500/20 text-rose-600 dark:text-rose-400 text-xs font-medium cursor-help"
                title={sysStatus?.error_detail || "Local engine offline"}
              >
                <ShieldAlert className="w-4 h-4 text-rose-500 dark:text-rose-400" />
                <span>AI Engine: Offline</span>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};
