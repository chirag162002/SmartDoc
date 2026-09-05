import type {
  DocumentItem,
  DocumentAnalysis,
  Citation,
  WebCitation,
  ChatMessage,
  ComparisonMatrixItem,
  ComparisonResponse,
  SystemStatus,
} from "../types/api";

export type {
  DocumentItem,
  DocumentAnalysis,
  Citation,
  WebCitation,
  ChatMessage,
  ComparisonMatrixItem,
  ComparisonResponse,
  SystemStatus,
};

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

async function safeFetch(url: string, options?: RequestInit): Promise<Response> {
  try {
    return await fetch(url, options);
  } catch (error: unknown) {
    if (error instanceof TypeError && error.message.includes("fetch")) {
      throw new Error("Unable to connect to SmartDoc backend service. Please check your network connection or server status.");
    }
    throw error;
  }
}

export async function uploadDocument(file?: File, url?: string): Promise<DocumentItem> {
  const formData = new FormData();
  if (file) {
    formData.append("file", file);
  }
  if (url) {
    formData.append("url", url);
  }

  const res = await safeFetch(`${API_BASE_URL}/documents/upload`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: "Upload failed." }));
    throw new Error(errorData.detail || "Failed to upload document.");
  }

  return res.json();
}

export async function fetchDocuments(): Promise<DocumentItem[]> {
  const res = await safeFetch(`${API_BASE_URL}/documents`);
  if (!res.ok) throw new Error("Failed to fetch document list.");
  return res.json();
}

export async function fetchDocumentStatus(docId: string): Promise<{
  id: string;
  status: string;
  progress_percent: number;
  current_stage: string;
  error_message?: string;
}> {
  const res = await safeFetch(`${API_BASE_URL}/documents/${docId}/status`);
  if (!res.ok) throw new Error("Failed to fetch document status.");
  return res.json();
}

export async function fetchDocumentAnalysis(docId: string): Promise<DocumentAnalysis> {
  const res = await safeFetch(`${API_BASE_URL}/analysis/${docId}`);
  if (!res.ok) throw new Error("Failed to fetch document analysis.");
  return res.json();
}

export async function sendChatMessage(
  documentIds: string[],
  message: string,
  sessionId?: string
): Promise<ChatMessage> {
  const res = await safeFetch(`${API_BASE_URL}/chat/message`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      document_ids: documentIds,
      message,
      session_id: sessionId,
    }),
  });
  if (!res.ok) throw new Error("Failed to send chat message.");
  return res.json();
}

export async function sendWebSearchQuery(
  documentIds: string[],
  message: string,
  sessionId?: string
): Promise<ChatMessage> {
  const res = await safeFetch(`${API_BASE_URL}/chat/web-search`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      document_ids: documentIds,
      message,
      session_id: sessionId,
    }),
  });
  if (!res.ok) throw new Error("Failed to execute web search.");
  return res.json();
}

export async function compareDocuments(documentIds: string[]): Promise<ComparisonResponse> {
  const res = await safeFetch(`${API_BASE_URL}/analysis/compare`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ document_ids: documentIds }),
  });
  if (!res.ok) throw new Error("Failed to generate comparative analysis.");
  return res.json();
}

export async function deleteDocument(docId: string): Promise<void> {
  const res = await safeFetch(`${API_BASE_URL}/documents/${docId}`, { method: "DELETE" });
  if (!res.ok) throw new Error("Failed to delete document.");
}

export async function fetchSystemStatus(): Promise<SystemStatus> {
  const res = await safeFetch(`${API_BASE_URL}/system/status`);
  if (!res.ok) throw new Error("Failed to fetch system status.");
  return res.json();
}
