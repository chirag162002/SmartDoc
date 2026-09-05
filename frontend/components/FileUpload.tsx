"use client";

import React, { useState, useRef } from "react";
import {
  UploadCloud,
  Link as LinkIcon,
  FileCode,
  FileSpreadsheet,
  FileText,
  Image as ImageIcon,
  Presentation,
  CheckCircle2,
  AlertCircle,
  Loader2,
} from "lucide-react";

interface FileUploadProps {
  onUploadSuccess: (docId: string) => void;
}

export const FileUpload: React.FC<FileUploadProps> = ({ onUploadSuccess }) => {
  const [dragActive, setDragActive] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [urlInput, setUrlInput] = useState("");
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const processUpload = async (file?: File, url?: string) => {
    setIsUploading(true);
    setErrorMsg(null);

    try {
      const { uploadDocument } = await import("@/lib/api");
      const doc = await uploadDocument(file, url);
      onUploadSuccess(doc.id);
    } catch (err: unknown) {
      setErrorMsg((err as Error).message || "Failed to process file upload.");
    } finally {
      setIsUploading(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      processUpload(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      processUpload(e.target.files[0]);
    }
  };

  const handleUrlSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!urlInput.trim()) return;
    processUpload(undefined, urlInput.trim());
  };

  return (
    <div className="w-full max-w-4xl mx-auto space-y-6">
      {/* File Drag & Drop Card */}
      <div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => !isUploading && fileInputRef.current?.click()}
        className={`glass-panel glass-panel-hover relative p-10 rounded-2xl border-2 border-dashed text-center cursor-pointer transition-all ${
          dragActive
            ? "border-indigo-500 bg-indigo-500/10 scale-[1.01]"
            : "border-slate-300 dark:border-slate-800 hover:border-indigo-500/50"
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          className="hidden"
          onChange={handleFileChange}
          accept=".pdf,.docx,.doc,.xlsx,.xls,.csv,.tsv,.pptx,.ppt,.txt,.md,.png,.jpg,.jpeg,.webp,.html,.htm"
        />

        {isUploading ? (
          <div className="flex flex-col items-center justify-center space-y-4 py-4 animate-pulse">
            <div className="w-16 h-16 rounded-2xl bg-indigo-500/20 border border-indigo-500/40 flex items-center justify-center text-indigo-500 dark:text-indigo-400 shadow-xl">
              <Loader2 className="w-8 h-8 animate-spin" />
            </div>
            <div className="space-y-1 text-center">
              <h3 className="text-lg font-bold text-slate-900 dark:text-white">
                Parsing & Analyzing Document...
              </h3>
              <p className="text-xs text-indigo-600 dark:text-indigo-300">
                Extracting content, running OCR/tabular profiler & generating AI summary
              </p>
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center space-y-4">
            <div className="w-16 h-16 rounded-2xl bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-500 dark:text-indigo-400 group-hover:scale-110 transition-transform">
              <UploadCloud className="w-8 h-8" />
            </div>

            <div>
              <h3 className="text-lg font-semibold text-slate-900 dark:text-white">
                Drag & Drop your document here
              </h3>
              <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
                Supports virtually any format up to 100 MB
              </p>
            </div>

            <button
              type="button"
              disabled={isUploading}
              className="px-6 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-sm shadow-lg shadow-indigo-600/30 transition-all flex items-center gap-2 cursor-pointer"
            >
              Browse Files
            </button>
          </div>
        )}

        {/* Supported Formats Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-2.5 mt-8 pt-6 border-t border-slate-200/80 dark:border-slate-800/80">
          <div className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-slate-100 dark:bg-slate-900/90 border border-slate-200 dark:border-slate-700/80 text-slate-700 dark:text-slate-200 text-xs font-medium shadow-sm">
            <FileText className="w-3.5 h-3.5 text-rose-500 dark:text-rose-400" />
            PDF (OCR)
          </div>
          <div className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-slate-100 dark:bg-slate-900/90 border border-slate-200 dark:border-slate-700/80 text-slate-700 dark:text-slate-200 text-xs font-medium shadow-sm">
            <FileText className="w-3.5 h-3.5 text-blue-500 dark:text-blue-400" />
            Word (.docx)
          </div>
          <div className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-slate-100 dark:bg-slate-900/90 border border-slate-200 dark:border-slate-700/80 text-slate-700 dark:text-slate-200 text-xs font-medium shadow-sm">
            <FileSpreadsheet className="w-3.5 h-3.5 text-emerald-500 dark:text-emerald-400" />
            Excel / CSV
          </div>
          <div className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-slate-100 dark:bg-slate-900/90 border border-slate-200 dark:border-slate-700/80 text-slate-700 dark:text-slate-200 text-xs font-medium shadow-sm">
            <Presentation className="w-3.5 h-3.5 text-amber-500 dark:text-amber-400" />
            PowerPoint
          </div>
          <div className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-slate-100 dark:bg-slate-900/90 border border-slate-200 dark:border-slate-700/80 text-slate-700 dark:text-slate-200 text-xs font-medium shadow-sm">
            <ImageIcon className="w-3.5 h-3.5 text-purple-500 dark:text-purple-400" />
            Images (OCR)
          </div>
          <div className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-slate-100 dark:bg-slate-900/90 border border-slate-200 dark:border-slate-700/80 text-slate-700 dark:text-slate-200 text-xs font-medium shadow-sm">
            <FileCode className="w-3.5 h-3.5 text-indigo-500 dark:text-indigo-400" />
            Text / MD
          </div>
          <div className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-slate-100 dark:bg-slate-900/90 border border-slate-200 dark:border-slate-700/80 text-slate-700 dark:text-slate-200 text-xs font-medium shadow-sm">
            <LinkIcon className="w-3.5 h-3.5 text-teal-500 dark:text-teal-400" />
            Web / HTML
          </div>
        </div>
      </div>

      {/* Web URL Fetcher Card */}
      <div className="glass-panel p-5 rounded-2xl border border-slate-200 dark:border-slate-800">
        <form onSubmit={handleUrlSubmit} className="flex flex-col sm:flex-row items-center gap-3">
          <div className="flex-1 w-full relative">
            <LinkIcon className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="url"
              value={urlInput}
              onChange={(e) => setUrlInput(e.target.value)}
              placeholder="Or paste web page URL (e.g. https://example.com/article)..."
              className="w-full bg-slate-100 dark:bg-slate-900/90 border border-slate-300 dark:border-slate-800 focus:border-indigo-500 rounded-xl pl-10 pr-4 py-2.5 text-sm text-slate-900 dark:text-white placeholder-slate-400 dark:placeholder-slate-500 outline-none transition-colors"
            />
          </div>
          <button
            type="submit"
            disabled={isUploading || !urlInput.trim()}
            className="w-full sm:w-auto px-5 py-2.5 rounded-xl bg-slate-800 dark:bg-slate-800 hover:bg-slate-700 disabled:opacity-50 text-white font-medium text-sm transition-all cursor-pointer"
          >
            Extract Web URL
          </button>
        </form>
      </div>

      {/* Error Message Alert */}
      {errorMsg && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-sm flex items-center gap-3">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}
    </div>
  );
};
