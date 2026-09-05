export interface DocumentItem {
  id: string;
  filename: string;
  original_name: string;
  file_type: string;
  file_size_bytes: number;
  status: string;
  progress_percent: number;
  current_stage: string;
  error_message?: string;
  page_count: number;
  created_at: string;
  updated_at: string;
}

export interface EntityItem {
  category: string;
  value: string;
  count: number;
}

export interface KeyNumberDateItem {
  value: string;
  label: string;
  page?: number;
  citation?: string;
}

export interface RiskFlagItem {
  risk: string;
  severity: "HIGH" | "MEDIUM" | "LOW" | string;
  citation?: string;
  description?: string;
}

export interface ActionItem {
  item: string;
  priority?: "HIGH" | "MEDIUM" | "LOW" | string;
  owner?: string;
}

export interface ColumnStats {
  mean?: number;
  min?: number;
  max?: number;
  sum?: number;
  count?: number;
  null_count?: number;
}

export interface TabularSheetData {
  row_count?: number;
  col_count?: number;
  columns?: string[];
  numeric_stats?: Record<string, ColumnStats>;
}

export interface SentimentTone {
  overall?: string;
  confidence?: number;
  tone_attributes?: string[];
}

export interface DocumentAnalysis {
  document_id: string;
  executive_summary: string;
  detailed_summary: string;
  entities: EntityItem[];
  topics: string[];
  sentiment_tone: SentimentTone;
  key_numbers_dates: KeyNumberDateItem[];
  risk_flags: RiskFlagItem[];
  action_items: ActionItem[];
  tabular_metrics?: Record<string, TabularSheetData>;
  is_fallback?: boolean;
  fallback_notice?: string;
  created_at: string;
}

export interface Citation {
  doc_id: string;
  chunk_id: string;
  page_number?: number;
  snippet: string;
}

export interface WebCitation {
  title: string;
  url: string;
  snippet?: string;
}

export interface ChatMessage {
  session_id: string;
  message_id: string;
  sender: "user" | "assistant";
  content: string;
  citations: Citation[];
  offer_web_search?: boolean;
  web_search_prompt?: string;
  is_web_result?: boolean;
  web_citations?: WebCitation[];
  original_query?: string;
  created_at: string;
}

export interface ComparisonMatrixItem {
  document_id: string;
  filename: string;
  file_type: string;
  executive_summary: string;
  key_metrics: string[];
  top_risks: string[];
}

export interface ComparisonResponse {
  comparative_summary: string;
  key_differences: string[];
  matrix: ComparisonMatrixItem[];
}

export interface SystemStatus {
  status: string;
  provider: string;
  model: string;
  is_online: boolean;
  error_detail?: string;
}
