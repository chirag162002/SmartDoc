"use client";

import React, { useState, useEffect } from "react";
import { Navbar } from "@/components/Navbar";
import { FileUpload } from "@/components/FileUpload";
import { ProcessingStepper } from "@/components/ProcessingStepper";
import { AnalysisDashboard } from "@/components/AnalysisDashboard";
import { DocumentLibrary } from "@/components/DocumentLibrary";
import { MultiDocComparison } from "@/components/MultiDocComparison";
import { DocumentItem, fetchDocuments, deleteDocument } from "@/lib/api";

export default function Home() {
  const [activeTab, setActiveTab] = useState<"dashboard" | "library" | "compare">("dashboard");
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [activeDocId, setActiveDocId] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [selectedDocForAnalysis, setSelectedDocForAnalysis] = useState<DocumentItem | null>(null);

  const loadDocuments = async () => {
    try {
      const list = await fetchDocuments();
      setDocuments(list);
    } catch (err: unknown) {
      console.error("Error fetching documents:", err);
    }
  };

  useEffect(() => {
    loadDocuments();
  }, []);

  const handleUploadSuccess = (docId: string) => {
    setActiveDocId(docId);
    setIsProcessing(true);
    setSelectedDocForAnalysis(null);
    loadDocuments();
  };

  const handleProcessingComplete = async () => {
    setIsProcessing(false);
    await loadDocuments();
    if (activeDocId) {
      const updatedList = await fetchDocuments();
      const match = updatedList.find((d) => d.id === activeDocId);
      if (match) {
        setSelectedDocForAnalysis(match);
      }
    }
  };

  const handleSelectDocument = (doc: DocumentItem) => {
    setSelectedDocForAnalysis(doc);
    setActiveTab("dashboard");
  };

  const handleDeleteDocument = async (docId: string) => {
    try {
      await deleteDocument(docId);
      if (selectedDocForAnalysis?.id === docId) {
        setSelectedDocForAnalysis(null);
      }
      loadDocuments();
    } catch (err) {
      console.error("Failed to delete document:", err);
    }
  };

  return (
    <div className="min-h-screen bg-[#f8fafc] dark:bg-[#090D16] text-slate-800 dark:text-slate-100 pb-16 transition-colors">
      {/* Top Navigation Bar */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={(tab) => {
          setActiveTab(tab);
          if (tab !== "dashboard") {
            setSelectedDocForAnalysis(null);
          }
        }}
        documentCount={documents.length}
      />

      <main className="max-w-7xl mx-auto px-6">
        {/* VIEW 1: Dashboard / Workspace */}
        {activeTab === "dashboard" && (
          <div className="space-y-8">
            {selectedDocForAnalysis ? (
              <AnalysisDashboard
                document={selectedDocForAnalysis}
                onBack={() => setSelectedDocForAnalysis(null)}
              />
            ) : isProcessing && activeDocId ? (
              <ProcessingStepper docId={activeDocId} onComplete={handleProcessingComplete} />
            ) : (
              <div className="space-y-12">
                {/* Hero Banner */}
                <div className="text-center max-w-3xl mx-auto space-y-4 pt-4">
                  <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-600 dark:text-indigo-300 text-xs font-semibold">
                    ✨ Multi-Format Intelligent Extraction Engine
                  </div>
                  <h1 className="text-4xl sm:text-5xl font-extrabold text-slate-900 dark:text-white tracking-tight leading-tight">
                    Extract, Summarize & Analyze Any Document with AI
                  </h1>
                  <p className="text-base text-slate-600 dark:text-slate-400">
                    Upload PDFs, Word, Spreadsheets, Presentation decks, Images, or Web URLs. Get
                    zero-hallucination grounded summaries and interactive chat with source
                    citations.
                  </p>
                </div>

                {/* Upload Zone */}
                <FileUpload onUploadSuccess={handleUploadSuccess} />

                {/* Quick Recent Library View */}
                {documents.length > 0 && (
                  <div className="pt-6">
                    <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">
                      Recent Documents
                    </h3>
                    <DocumentLibrary
                      documents={documents.slice(0, 5)}
                      onSelectDocument={handleSelectDocument}
                      onDeleteDocument={handleDeleteDocument}
                    />
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* VIEW 2: Document Library */}
        {activeTab === "library" && (
          <DocumentLibrary
            documents={documents}
            onSelectDocument={handleSelectDocument}
            onDeleteDocument={handleDeleteDocument}
          />
        )}

        {/* VIEW 3: Multi-Document Comparison Workspace */}
        {activeTab === "compare" && <MultiDocComparison />}
      </main>
    </div>
  );
}
