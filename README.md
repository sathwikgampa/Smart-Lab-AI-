# SmartLab AI

[![Live Demo](https://img.shields.io/badge/Live%20Demo-smart--lab--ai.onrender.com-46E3B7?style=for-the-badge&logo=render&logoColor=white)](https://smart-lab-ai.onrender.com)
[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev)
[![Supabase PostgreSQL](https://img.shields.io/badge/Database-Supabase%20PostgreSQL-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white)](https://supabase.com)
[![License](https://img.shields.io/badge/License-MIT-purple?style=for-the-badge)](LICENSE)

> 🚀 **Live Production Deployment**: [https://smart-lab-ai.onrender.com](https://smart-lab-ai.onrender.com)  
> 🔗 **GitHub Repository**: [https://github.com/sathwikgampa/Smart-Lab-AI-](https://github.com/sathwikgampa/Smart-Lab-AI-)

---

## 📌 Project Description

**SmartLab AI** is an enterprise-grade, multimodal laboratory knowledge and operations assistant engineered specifically for pharmaceutical, biotechnology, and academic research environments. 

In traditional laboratories, scientists lose hundreds of hours annually to manual buffer calculations, cross-referencing conflicting standard operating procedures (SOPs), tracking down expiring reagents, and deciphering cryptic instrument error codes. Furthermore, calculation mistakes or incompatible chemical combinations introduce severe safety risks and costly experiment failures.

SmartLab AI solves these challenges by combining:
1. **Autonomous Lab Co-Pilot** with deterministic reasoning that calculates exact masses from chemical molecular weights, verifies real-time stock levels, and audits chemical compatibility before bench work begins.
2. **Zero-Hallucination Multimodal RAG** that ingests SOPs, protocols, and equipment manuals to answer scientific questions with verbatim, page-level citations.
3. **Computer Vision Hardware Diagnostics** that identifies instrument error codes from display screen photos, mapping them to manufacturer-approved fixes and PPE requirements.
4. **End-to-End Wet-Lab Workspace** covering chemical inventory, experiment protocol editors with peer review checkpoints, scientific dataset analytics, live kinetic simulations, and GxP-ready audit trails.

SmartLab AI operates **100% offline out-of-the-box** using local deterministic fallback engines, and can be seamlessly upgraded to Anthropic Claude (`claude-opus-5-5`) for advanced reasoning and multimodal image synthesis.

---

## 🌐 Live Demo & Quick Start

* **Public Web URL**: [https://smart-lab-ai.onrender.com](https://smart-lab-ai.onrender.com)
* **First-time Access**: Click **Sign Up** (`#/signup`) to create your account. The first registered user is automatically provisioned as the **Workspace Administrator**.
* **API Health Check**: [https://smart-lab-ai.onrender.com/api/health](https://smart-lab-ai.onrender.com/api/health)

---

## 🛠️ Complete Tech Stack

### Frontend Architecture
* **Core Framework**: React 18 (SPA with fast hash routing `#/`)
* **Build Tool & Bundler**: Vite 5
* **Styling & Design System**: Tailwind CSS with custom lab design tokens (WCAG AA contrast-checked, light/dark mode responsive)
* **Data Visualization & Charts**: Recharts (enzyme kinetics, dose-response curves, qPCR amplification)
* **Mathematical Rendering**: `react-markdown` with KaTeX ($LaTeX$ formula support)
* **Icons & UI Feedback**: Lucide React, accessible headless drawer & modal components

### Backend Architecture
* **Runtime**: Python 3.11+
* **Framework**: Flask 3.0+ Application Factory architecture
* **WSGI Production Server**: Gunicorn (Linux/Render production) & Waitress (Windows local)
* **API Architecture**: Modular REST Blueprints (`/api/auth`, `/api/chat`, `/api/documents`, `/api/reagents`, `/api/troubleshooting`, etc.) with Server-Sent Events (SSE) streaming (`/api/chat/stream`)
* **Security & Auth**: HTTP-only SameSite cookie sessions, salted scrypt password hashing, rate limiting, and CSRF/CORS origin guards

### AI, Machine Learning & RAG Engine
* **Large Language Models**: Anthropic Claude API (`claude-opus-5-5` with adaptive thinking) with deterministic rules-based offline fallback
* **Vector Store**: FAISS (`IndexIDMap` FlatIP) & NumPy fallback
* **Embedding Models**: Sentence-Transformers (`all-MiniLM-L6-v2`) with custom high-speed hashing embedder fallback
* **Document Parsing**: PyMuPDF (`fitz`) for PDF text layout extraction, header/footer cleansing, and exact page bounding
* **Computer Vision**: Multimodal image analysis for instrument error screens, OCR text extraction, and safety indicator heuristics
* **Guardrails**: Custom guardrail verification engine ([app/guardrails.py](backend/app/guardrails.py)) enforcing numerical verification, prompt injection quarantine, and strict non-hallucination policies

### Database & Storage
* **Dual-Engine Architecture**: 
  - **Cloud Production**: PostgreSQL on Supabase with connection pooling (`pooler.supabase.com`)
  - **Local Development**: SQLite (`smartlab.db`) with zero-configuration fallback
* **Database Adapter**: Custom SQLite-compatible wrapper for PostgreSQL with automated schema migrations
* **External Literature API**: Europe PMC scientific research literature search integration

### Cloud & DevOps
* **Hosting Platform**: Render Cloud (Oregon Region)
* **Deployment Format**: Unified Full-Stack Web Service (`render-build.sh` + `render.yaml`)
* **Edge CDN**: Cloudflare SSL/TLS termination, HTTP/3, and DDoS mitigation

---

## 📖 How to Use the Web App Features

### 1. 🧪 Ask Lab Co-Pilot (`#/ask`)
The central interactive laboratory assistant that plans and executes multi-step protocols with zero hallucination.
* **How to use**: Type a natural language command into the composer, such as:
  * *"Prepare 500 mL of 50 mM Tris-HCl buffer at pH 7.5"*
  * *"How long should trypsin-EDTA incubate when passaging HEK293 cells?"*
* **How it works**: The co-pilot runs an autonomous pipeline:
  `Plan ➔ Retrieve SOP ➔ Calculate Mass ➔ Check Inventory ➔ Chemical Compatibility Check ➔ Synthesize ➔ Verify`.
* **Trust Badges**:
  * `Supported by uploaded SOP`: Full confidence, in stock, zero incompatibility.
  * `Caution`: Non-blocking note (e.g. reagent expiring soon or unreviewed source).
  * `Refused`: Missing/expired stock or hazardous chemical incompatibility.

### 2. 📄 Documents & SOP Governance (`#/documents`)
Upload, index, and manage laboratory standard operating procedures and manuals.
* **How to use**: Click **Upload SOP**, select a PDF (up to 25 MB), assign category and document code, and submit.
* **Page-Level Citations**: When the AI answers any query, clicking the citation chip opens the **Evidence Panel** showing the exact source document, page number, and highlighted excerpt.
* **Approval Workflows**: Documents transition across `Approved`, `Pending Review`, `Outdated`, or `Unreviewed` states with complete version tracking.

### 3. 📦 Reagent Inventory & Chemical Safety (`#/reagents` & `#/safety`)
Real-time tracking of chemical stocks, lot numbers, storage locations, and hazard classes.
* **Stock Tracking**: Search reagents by name or formula (e.g., *Sodium Chloride*, *DTT*, *Tris Base*).
* **Consume & Restock**: Log reagent consumption directly; inventory balances never drop below zero.
* **Safety Matrix**: View chemical hazard classifications (GHS) and safety emergency contacts.

### 4. 🛠️ Hardware Diagnostics & Troubleshooting (`#/troubleshooting`)
Instant resolution for laboratory instrumentation faults (HPLCs, PCR thermocyclers, centrifuges, spectrophotometers).
* **Error Code Lookup**: Enter an error code (e.g., `E-104` or `ERR-02`) to view step-by-step resolution SOPs.
* **Display Photo OCR**: Attach a photograph of an instrument display screen; the vision engine extracts the error readout automatically.
* **Mandatory PPE Warnings**: The system outputs required Personal Protective Equipment (gloves, goggles, fume hoods) before anyone touches the instrument.

### 5. 🔬 Experiment Protocols & Peer Reviews (`#/experiments`)
Interactive protocol execution studio.
* **Protocol Editor**: Write and edit protocols using Markdown and LaTeX equations with live side-by-side preview.
* **Bench Checklists**: Check off procedural steps as they are completed with progress bars.
* **Peer Review Checkpoints**: Request reviews from colleagues (Protocol approval, Safety sign-off, Data review) with sign-off comments.

### 6. 📊 Scientific Datasets & Data Analytics (`#/data`)
Manage and visualize wet-lab assay data.
* **CSV Import**: Upload raw experimental datasets (e.g., enzyme kinetics, qPCR amplification, cell viability assays).
* **Interactive Visualizations**: Server-side filtering, column statistics (mean, median, standard deviation), and dynamic scatter/bar charts.

### 7. 📈 Protocol Simulations (`#/simulation`)
Conduct virtual dry-runs before committing costly reagents.
* **Simulate Assays**: Test experimental parameters with interactive sliders:
  * **Michaelis-Menten Kinetics**: Vary $V_{max}$, $K_m$, and competitive inhibitors.
  * **qPCR Amplification**: Model cycle threshold ($C_t$) curves and primer efficiency.
  * **4PL Dose-Response**: Model $IC_{50}$ curves and hill slopes.
  * **Bacterial Growth**: Model temperature-dependent growth kinetics.

### 8. 👥 Team Collaboration & Audit Trail (`#/collaboration` & `#/activity`)
GxP-ready compliance and team coordination.
* **Project Workspaces**: Group experiments, protocols, and datasets under dedicated projects.
* **Threaded Comments**: Discuss protocols directly within notebook threads.
* **Audit Trail**: Every document approval, inventory modification, user action, and AI query is permanently logged with timestamps.

---

## 🚀 Production Deployment Architecture

SmartLab AI is deployed as a **Single-Origin Unified Full-Stack Application** on Render:

```
                  ┌────────────────────────────────────────┐
                  │          Cloudflare Edge (HTTPS)       │
                  │       smart-lab-ai.onrender.com        │
                  └───────────────────┬────────────────────┘
                                      │
                                      ▼
                  ┌────────────────────────────────────────┐
                  │      Render Production Web Service     │
                  │   (Gunicorn WSGI - Python 3.11 Linux)  │
                  ├───────────────────┬────────────────────┤
                  │   Static Frontend │   Flask REST API   │
                  │   (/assets/*, /)  │     (/api/*)       │
                  │   (React 18 SPA)  │ (Agent Orchestrator│
                  └───────────────────┼────────────────────┘
                                      │
                                      ▼
                  ┌────────────────────────────────────────┐
                  │       Supabase Cloud PostgreSQL        │
                  │   (aws-0-ap-northeast-2.pooler)        │
                  │  (Users, SOPs, Lots, Datasets, Audit)  │
                  └────────────────────────────────────────┘
```

### Key Production Features
1. **Single-Origin Efficiency**: Flask automatically serves the compiled Vite assets from `frontend/dist/` alongside `/api/*`, avoiding third-party cookie restrictions, CORS overhead, and desynchronized cold starts.
2. **Cloud Database Pooling**: Utilizes Supabase IPv4 connection pooling with SSL encryption (`sslmode=require`).
3. **Session Security**: HttpOnly `SameSite=Lax` cookies with SHA-256 token hashing and salted scrypt passwords.
4. **Resilient Vector Store**: Persisted NumPy/FAISS indices with dynamic background re-indexing.

---

## 💻 Local Development Setup

### Prerequisites
* Python **3.10+** (tested on 3.11 and 3.14)
* Node.js **18+** (tested on 20 and 24)

### 1. Clone & Configure
```bash
git clone https://github.com/sathwikgampa/Smart-Lab-AI-.git
cd Smart-Lab-AI-
cp .env.example .env
```

### 2. Backend Setup
```bash
cd backend
python -m venv .venv

# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
python run.py    # Starts API on http://127.0.0.1:5000
```

### 3. Frontend Setup
```bash
cd ../frontend
npm install
npm run dev      # Starts Vite dev server on http://localhost:5173
```

### 4. Running Tests
Run the comprehensive 380-test test suite:
```bash
cd ../backend
python -m pytest   # ~30s offline test suite
```

---

## 📄 License & Attribution

This project is open-source under the **MIT License**.  
Developed for the **AI Hackathon 2026** by the SmartLab AI team.
