"use client";

import React, { useEffect, useState } from "react";
import {
  CheckCircle2,
  Loader2,
  AlertTriangle,
  FileText,
  Cpu,
  Layers,
  Sparkles,
} from "lucide-react";
import { fetchDocumentStatus } from "@/lib/api";

interface ProcessingStepperProps {
  docId: string;
  onComplete: () => void;
}

export const ProcessingStepper: React.FC<ProcessingStepperProps> = ({ docId, onComplete }) => {
  const [status, setStatus] = useState<string>("PENDING");
  const [progress, setProgress] = useState<number>(10);
  const [currentStage, setCurrentStage] = useState<string>("Reading document file...");
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    let intervalId: ReturnType<typeof setInterval> | null = null;
    let isMounted = true;
    let consecutiveFailures = 0;

    const checkStatus = async () => {
      try {
        const data = await fetchDocumentStatus(docId);
        if (!isMounted) return;
        consecutiveFailures = 0;
        setStatus(data.status);
        setProgress(data.progress_percent);
        setCurrentStage(data.current_stage);

        if (data.status === "COMPLETE") {
          if (intervalId) clearInterval(intervalId);
          setTimeout(() => {
            if (isMounted) onComplete();
          }, 800);
        } else if (data.status === "FAILED") {
          if (intervalId) clearInterval(intervalId);
          setErrorMsg(data.error_message || "Document processing failed.");
        }
      } catch (err: unknown) {
        if (!isMounted) return;
        consecutiveFailures++;
        console.warn(`Status polling attempt ${consecutiveFailures} failed:`, err);
        if (consecutiveFailures >= 10) {
          if (intervalId) clearInterval(intervalId);
          setErrorMsg("Unable to reach backend service. Please check your network connection.");
        }
      }
    };

    checkStatus();
    intervalId = setInterval(checkStatus, 1500);

    return () => {
      isMounted = false;
      if (intervalId) clearInterval(intervalId);
    };
  }, [docId, onComplete]);

  const getEstimatedTime = () => {
    if (progress < 25) return "Est. time remaining: ~15-20s (Reading file)";
    if (progress < 60) return "Est. time remaining: ~10-15s (Extracting & profiling)";
    if (progress < 95) return "Est. time remaining: ~5-10s (Synthesizing summary)";
    return "Finalizing document analysis...";
  };

  return (
    <div className="w-full max-w-3xl mx-auto glass-panel p-8 rounded-2xl border border-slate-200 dark:border-slate-800 space-y-6 transition-colors">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-indigo-500/20 border border-indigo-500/30 flex items-center justify-center text-indigo-600 dark:text-indigo-400">
            {status === "FAILED" ? (
              <AlertTriangle className="w-5 h-5 text-rose-500 dark:text-rose-400" />
            ) : status === "COMPLETE" ? (
              <CheckCircle2 className="w-5 h-5 text-emerald-500 dark:text-emerald-400" />
            ) : (
              <Loader2 className="w-5 h-5 animate-spin text-indigo-600 dark:text-indigo-400" />
            )}
          </div>
          <div>
            <h3 className="text-lg font-bold text-slate-900 dark:text-white">
              {status === "FAILED"
                ? "Processing Failed"
                : status === "COMPLETE"
                  ? "Analysis Complete"
                  : "Analyzing Document..."}
            </h3>
            <p className="text-xs text-slate-600 dark:text-slate-400 mt-0.5">{currentStage}</p>
            {status !== "COMPLETE" && status !== "FAILED" && (
              <p className="text-[11px] text-indigo-600 dark:text-indigo-300 font-medium mt-1">
                ⏱️ {getEstimatedTime()}
              </p>
            )}
          </div>
        </div>
        <span className="text-2xl font-bold font-mono text-indigo-600 dark:text-indigo-400">
          {progress}%
        </span>
      </div>

      {/* Progress Bar */}
      <div className="w-full bg-slate-200 dark:bg-slate-900 rounded-full h-3 p-0.5 border border-slate-300 dark:border-slate-800 overflow-hidden">
        <div
          className="h-full bg-gradient-to-r from-indigo-600 via-indigo-500 to-emerald-400 rounded-full transition-all duration-500 ease-out shadow-lg shadow-indigo-500/20"
          style={{ width: `${progress}%` }}
        />
      </div>

      {/* Stage Stepper Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 pt-2 text-xs font-medium">
        <div
          className={`p-3 rounded-xl border text-center transition-all ${progress >= 15 ? "bg-indigo-500/10 border-indigo-500/30 text-indigo-700 dark:text-indigo-300 font-semibold" : "bg-slate-100 dark:bg-slate-900/40 border-slate-200 dark:border-slate-800 text-slate-500"}`}
        >
          <FileText className="w-4 h-4 mx-auto mb-1 text-indigo-500" />
          1. Reading File
        </div>
        <div
          className={`p-3 rounded-xl border text-center transition-all ${progress >= 35 ? "bg-indigo-500/10 border-indigo-500/30 text-indigo-700 dark:text-indigo-300 font-semibold" : "bg-slate-100 dark:bg-slate-900/40 border-slate-200 dark:border-slate-800 text-slate-500"}`}
        >
          <Cpu className="w-4 h-4 mx-auto mb-1 text-blue-500" />
          2. Extracting Text
        </div>
        <div
          className={`p-3 rounded-xl border text-center transition-all ${progress >= 60 ? "bg-indigo-500/10 border-indigo-500/30 text-indigo-700 dark:text-indigo-300 font-semibold" : "bg-slate-100 dark:bg-slate-900/40 border-slate-200 dark:border-slate-800 text-slate-500"}`}
        >
          <Layers className="w-4 h-4 mx-auto mb-1 text-purple-500" />
          3. Analyzing Content
        </div>
        <div
          className={`p-3 rounded-xl border text-center transition-all ${progress >= 100 ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-700 dark:text-emerald-300 font-semibold" : "bg-slate-100 dark:bg-slate-900/40 border-slate-200 dark:border-slate-800 text-slate-500"}`}
        >
          <Sparkles className="w-4 h-4 mx-auto mb-1 text-emerald-500" />
          4. Finalizing Summary
        </div>
      </div>

      {/* Error Alert */}
      {errorMsg && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-600 dark:text-rose-400 text-sm flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 flex-shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}
    </div>
  );
};
