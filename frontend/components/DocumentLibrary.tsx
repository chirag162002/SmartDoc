"use client";

import React from "react";
import {
  FileText,
  CheckCircle2,
  Clock,
  AlertTriangle,
  Trash2,
  Eye,
  FileSpreadsheet,
  Presentation,
  Image as ImageIcon,
  Link as LinkIcon,
  FileCode,
} from "lucide-react";
import { DocumentItem } from "@/lib/api";

interface DocumentLibraryProps {
  documents: DocumentItem[];
  onSelectDocument: (doc: DocumentItem) => void;
  onDeleteDocument: (docId: string) => void;
}

export const DocumentLibrary: React.FC<DocumentLibraryProps> = ({
  documents,
  onSelectDocument,
  onDeleteDocument,
}) => {
  const getFileIcon = (fileType: string) => {
    switch (fileType.toLowerCase()) {
      case "pdf":
        return <FileText className="w-5 h-5 text-rose-400" />;
      case "docx":
      case "doc":
        return <FileText className="w-5 h-5 text-blue-400" />;
      case "xlsx":
      case "xls":
      case "csv":
      case "tsv":
      case "excel":
        return <FileSpreadsheet className="w-5 h-5 text-emerald-400" />;
      case "pptx":
      case "ppt":
        return <Presentation className="w-5 h-5 text-amber-400" />;
      case "image":
      case "png":
      case "jpg":
        return <ImageIcon className="w-5 h-5 text-purple-400" />;
      case "html":
        return <LinkIcon className="w-5 h-5 text-teal-400" />;
      default:
        return <FileCode className="w-5 h-5 text-indigo-400" />;
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="w-full max-w-6xl mx-auto glass-panel p-6 rounded-2xl border border-slate-200 dark:border-slate-800 space-y-6 transition-colors">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <FileText className="w-6 h-6 text-indigo-600 dark:text-indigo-400" />
            Document Library
          </h2>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Manage your uploaded documents and view extracted intelligence.
          </p>
        </div>
        <span className="text-xs px-3 py-1 bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-200 rounded-full font-mono font-semibold">
          {documents.length} document(s)
        </span>
      </div>

      {documents.length === 0 ? (
        <div className="text-center py-16 text-slate-500 dark:text-slate-400 space-y-3">
          <FileText className="w-12 h-12 text-slate-400 dark:text-slate-500 mx-auto" />
          <p className="text-sm font-medium text-slate-800 dark:text-slate-200">
            No documents uploaded yet.
          </p>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Upload a PDF, Word, Excel, PPTX, or Image file to get started.
          </p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-sm">
            <thead>
              <tr className="border-b border-slate-200 dark:border-slate-800 text-slate-700 dark:text-slate-300 text-xs font-bold uppercase tracking-wider">
                <th className="py-3 px-4">Document</th>
                <th className="py-3 px-4">Format</th>
                <th className="py-3 px-4">Pages / Size</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200/80 dark:divide-slate-800/60">
              {documents.map((doc) => (
                <tr
                  key={doc.id}
                  className="hover:bg-slate-100/80 dark:hover:bg-slate-800/60 transition-colors group"
                >
                  <td className="py-3.5 px-4 font-medium text-slate-900 dark:text-white flex items-center gap-3">
                    {getFileIcon(doc.file_type)}
                    <span className="truncate max-w-[280px] text-slate-900 dark:text-white font-semibold group-hover:text-indigo-600 dark:group-hover:text-indigo-300 transition-colors">
                      {doc.original_name}
                    </span>
                  </td>

                  <td className="py-3.5 px-4">
                    <span className="text-xs px-2.5 py-0.5 rounded bg-slate-100 dark:bg-slate-900 text-slate-800 dark:text-slate-200 border border-slate-200 dark:border-slate-700 uppercase font-mono font-semibold">
                      {doc.file_type}
                    </span>
                  </td>

                  <td className="py-3.5 px-4 text-slate-600 dark:text-slate-300 text-xs font-mono font-medium">
                    {doc.page_count > 0
                      ? `${doc.page_count} pg(s)`
                      : formatFileSize(doc.file_size_bytes)}
                  </td>

                  <td className="py-3.5 px-4">
                    {doc.status === "COMPLETE" ? (
                      <span className="inline-flex items-center gap-1.5 text-xs text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 px-2.5 py-1 rounded-full border border-emerald-500/20 font-medium">
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        Complete
                      </span>
                    ) : doc.status === "FAILED" ? (
                      <span className="inline-flex items-center gap-1.5 text-xs text-rose-600 dark:text-rose-400 bg-rose-500/10 px-2.5 py-1 rounded-full border border-rose-500/20 font-medium">
                        <AlertTriangle className="w-3.5 h-3.5" />
                        Failed
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1.5 text-xs text-amber-600 dark:text-amber-400 bg-amber-500/10 px-2.5 py-1 rounded-full border border-amber-500/20 font-medium">
                        <Clock className="w-3.5 h-3.5 animate-spin" />
                        {doc.progress_percent}% Processing
                      </span>
                    )}
                  </td>

                  <td className="py-3.5 px-4 text-right space-x-2">
                    {doc.status === "COMPLETE" && (
                      <button
                        onClick={() => onSelectDocument(doc)}
                        className="px-3 py-1.5 rounded-lg bg-indigo-500/10 dark:bg-indigo-600/20 hover:bg-indigo-600 hover:text-white text-indigo-700 dark:text-indigo-300 text-xs font-medium border border-indigo-500/30 transition-all inline-flex items-center gap-1.5 cursor-pointer"
                      >
                        <Eye className="w-3.5 h-3.5" />
                        View Analysis
                      </button>
                    )}
                    <button
                      onClick={() => onDeleteDocument(doc.id)}
                      className="p-1.5 rounded-lg text-slate-400 dark:text-slate-500 hover:text-rose-500 hover:bg-rose-500/10 transition-all inline-flex items-center cursor-pointer"
                      title="Delete document"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
