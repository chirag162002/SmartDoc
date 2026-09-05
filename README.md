# SmartDoc — Universal Document Intelligence & Grounded Analysis Platform

**SmartDoc** is an enterprise-grade document intelligence platform designed to extract, profile, analyze, and query complex multi-format documents (PDF, DOCX, XLSX, PPTX, HTML, and OCR-scanned Images). 

It combines deterministic document extraction with a strict, citation-validated Grounded AI answering engine, statistical dataset profiling, and an opt-in live web search fallback.

---

## 🌟 Key Capabilities

- 📄 **Multi-Format Extraction Pipeline**:
  - **PDF**: Text, page layout preservation, and structural extraction.
  - **Word (`.docx`) & PowerPoint (`.pptx`)**: Structured document hierarchy and slide text.
  - **Excel & CSV (`.xlsx`, `.csv`)**: Automated pandas data profiling, separating quantitative key performance metrics (totals, means, ranges) from unique categorical identifiers (Order IDs, GSTIN, SKUs).
  - **Web & Scraped HTML**: Semantic content extraction with tag cleaning.
  - **OCR Image Scanner (`.png`, `.jpg`, `.tiff`)**: Integrated Tesseract OCR engine for scanned paper records.

- 🔍 **Page-Aware Citation & Grounded Answering**:
  - Preserves precise document boundaries (`Page 1`, `Page 2`, etc.) throughout chunking.
  - Fact-checking layer validates generated numerical facts, dates, and currency values against source context to eliminate LLM hallucinations.

- 🌐 **Opt-in Live Web Search Fallback**:
  - Automatically identifies when document context is insufficient for a query and synthesizes real-time web search results (via Tavily / DuckDuckGo API) with domain citations.

- 📊 **Multi-Document Comparative Analysis**:
  - Side-by-side comparison matrix across multiple documents for cross-referencing metrics, key entities, and risk factors.

- 🎨 **Modern Responsive UI**:
  - Built with Next.js 16, Tailwind CSS, Lucide Icons, and React.
  - Light and dark themes with auto-detect default light mode.

---

## 🏗️ System Architecture

```
  ┌─────────────────────────────────────────────────────────────┐
  │                   Next.js 16 React Client                   │
  │     (Dashboard, File Upload, Stepper, Grounded Chat)        │
  └──────────────────────────────┬──────────────────────────────┘
                                 │ REST API / JSON
  ┌──────────────────────────────▼──────────────────────────────┐
  │                     FastAPI Backend Layer                   │
  ├──────────────────────────────┬──────────────────────────────┤
  │ Document Ingestion Service   │ Chat & Verification Service  │
  │ Router & Extractor Engine    │ Fact Checker Guardrails      │
  │ Page-Aware Chunker           │ LLM Orchestrator (Ollama)    │
  └──────────────────────────────┬──────────────────────────────┘
                                 │ Storage & DB
  ┌──────────────────────────────▼──────────────────────────────┐
  │             SQLite Database + Local Upload Storage          │
  └─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Getting Started

### Prerequisites

- **Python**: `3.10` or higher
- **Node.js**: `18.x` or higher
- **Ollama**: (Optional for local AI execution) Installed and running `llama3.2` model locally (`ollama run llama3.2`)

---

### 1. Backend Setup

```bash
# Clone the repository
git clone https://github.com/your-username/SmartDoc.git
cd SmartDoc/backend

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

#### Environment Configuration (`backend/.env`)

Create a `.env` file inside `backend/`:

```env
PROJECT_NAME="SmartDoc API"
VERSION="1.0.0"
LLM_PROVIDER="ollama"
OLLAMA_BASE_URL="http://localhost:11434"
OLLAMA_MODEL="llama3.2"
WEB_SEARCH_ENABLED=true
TAVILY_API_KEY=""
```

#### Run Backend Server

```bash
python -m uvicorn app.main:app --reload --port 8000
```
*API interactive documentation will be available at `http://localhost:8000/docs`.*

---

### 2. Frontend Setup

```bash
cd ../frontend

# Install node dependencies
npm install

# Start Next.js development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## 🧪 Testing & Code Quality

### Backend Pytest Suite
```bash
cd backend
python -m pytest --cov=app --cov-report=term-missing
```

### Formatting & Linting
```bash
# Backend (Ruff & Black)
cd backend
ruff check . --fix
black .

# Frontend (ESLint & Prettier)
cd frontend
npm run lint
npm run format
```

### Pre-commit Hooks Setup
```bash
pre-commit install
```

---

## 🛣️ API Endpoints Summary

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/documents/upload` | Upload & enqueue document processing |
| `GET` | `/api/v1/documents` | List all processed documents |
| `GET` | `/api/v1/documents/{id}/status` | Check processing stage status & progress |
| `GET` | `/api/v1/analysis/{id}` | Get extracted summary, entities & tabular stats |
| `POST` | `/api/v1/chat/message` | Submit grounded RAG query with page citations |
| `POST` | `/api/v1/chat/web-search` | Submit query for live web search synthesis |
| `POST` | `/api/v1/analysis/compare` | Generate multi-document comparison matrix |
| `GET` | `/api/v1/system/status` | Backend health & LLM model connectivity check |

---

## 📜 License
Distributed under the MIT License. See `LICENSE` for more information.
