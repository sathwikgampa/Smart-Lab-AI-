# SmartLab AI

[![Live Demo](https://img.shields.io/badge/Live%20Demo-smart--lab--ai.onrender.com-46E3B7?style=for-the-badge&logo=render&logoColor=white)](https://smart-lab-ai.onrender.com)
[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev)
[![Supabase PostgreSQL](https://img.shields.io/badge/Database-Supabase%20PostgreSQL-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white)](https://supabase.com)

> 🚀 **Live Production Deployment**: [https://smart-lab-ai.onrender.com](https://smart-lab-ai.onrender.com)

**Multimodal Laboratory Knowledge & Operations Assistant** for pharma, biotech, and academic research laboratories.

SmartLab AI answers complex wet-lab questions from your Standard Operating Procedures (SOPs) and manuals with page-level citations. It analyses photos of equipment displays and samples, links them to verified-fix SOP pages, runs deterministic preparation and molarity math with chemical compatibility guards, and powers day-to-day lab workflows: reagent inventory, troubleshooting, experiment planning with expert review, scientific datasets, team collaboration, and protocol simulation.

It runs **fully offline** out of the box with deterministic fallbacks. Set `ANTHROPIC_API_KEY` to upgrade answer synthesis, image description, and literature summaries to Claude (`claude-opus-5-5`).

---

## Features

| Area | What it does | Where |
|---|---|---|
| **RAG knowledge chat** | Q&A over uploaded PDFs; Markdown + LaTeX answers | `backend/app/rag/engine.py`, `ChatView.jsx` |
| **Page-level citations** | Every grounded answer cites `document, page`. Citations are checked against the stored chunks, invented source ids are dropped, and an answer with no valid citation is never shown as grounded | `renumber_citations`, `verify_citations` |
| **Uncertainty handling** | A similarity threshold decides what counts as evidence. Answers are labelled `grounded` / `partial` / `insufficient` and list missing terms. "INSUFFICIENT_EVIDENCE" from the LLM is respected | `RAGEngine.answer` |
| **Image-to-document RAG** | A photo becomes an observational description plus verbatim display text, which drives SOP retrieval and verified-fix matching | `backend/app/vision/analyzer.py`, `VisionView.jsx` |
| **Vision guardrails** | The prompt forbids identifying chemicals, organisms, contaminants or medical conditions, and the output is sanitised (redacted and flagged). Queries asking for identification, medical dosing or interlock bypass are flagged | `backend/app/guardrails.py` |
| **Unified search** | One query searches SOP text, the reagent inventory and the troubleshooting database | `/api/search/unified`, `SearchView.jsx` |
| **Reagents** | Stock, expiry, storage and hazard data; low-stock/expiry status; consume and restock (never below zero); plain-English questions such as "where is trypsin stored?" | `services/inventory.py`, `ReagentsView.jsx` |
| **Troubleshooting** | Error code + keyword matching to verified, SOP-referenced fixes. New entries stay unverified until reviewed | `services/troubleshooting.py` |
| **Experiments** | Markdown/LaTeX protocol editor with live preview, reorderable checklist with progress, variable log | `api/experiments.py`, `ExperimentsView.jsx` |
| **Expert review** | Checkpoints (protocol, safety, data...) with approve / request changes. Notes are required to reject, and experiment status rolls up automatically | `/api/experiments/<id>/reviews` |
| **Data & analysis** | Datasets with server-side sort, filter and range filters, per-column statistics, CSV import, bar and scatter charts | `api/data.py`, `DataView.jsx` |
| **Collaboration** | Projects, threaded comments, drag-and-drop file sharing, live activity feed (5 s polling) | `api/collaboration.py`, `CollaborationView.jsx` |
| **Literature** | Europe PMC search → grounded summaries → cross-reference to internal SOPs (offline sample corpus fallback) | `services/literature.py` |
| **Simulation (LXS)** | Michaelis-Menten (+ inhibitor), qPCR amplification/Ct, temperature-dependent growth, 4PL dose-response, all with live sliders | `services/simulation.py`, `SimulationView.jsx` |
| **Document governance** | Category, document code, version, owner and approval status (approved / pending / outdated / unreviewed). Uploads start Unreviewed. When several versions of a document match, the approved one is used and the conflict is reported. Unapproved cited sources make the answer *partial* and ask for verification | `rag/engine.py: resolve_versions`, `api/documents.py` |
| **Expert review of answers** | Rate answers; *incorrect / unsafe / outdated* reports (with a required note) enter a review queue that a reviewer resolves | `/api/messages/<id>/feedback`, `/api/feedback` |
| **Audit trail** | Approval changes, uploads, re-indexing, deletions, inventory changes, settings edits and review resolutions | `audit_log` table, `/api/activity` |
| **Safety resources** | Safety-category documents with version and review date, a passage search limited to safety documents, recorded hazard classes, and emergency contacts entered by the institution (never invented) | `api/safety.py`, `SafetyView.jsx` |
| **Lab tour & profiles** | Floor-plan hotspots with step-by-step equipment training linked to SOPs; researcher progress and review queues | `api/profiles.py`, `LabTourView.jsx` |

### Interface

A light-first interface built around the evidence workflow (design tokens in `frontend/tailwind.config.js`, contrast-checked to WCAG AA).

- **Shell:** a dark navigation sidebar (collapsible on desktop, a drawer on mobile) with the core pages first: Overview, Ask SmartLab, Documents, Reagents, Scientific literature and Safety resources. Below them are *Lab operations* and *Early features* (collaboration, simulation, training), labelled as limited-scope prototypes, then Recent activity and Settings. The top bar has global search. Routes are hash URLs (`#/documents/12?page=3`), so deep links and the back button work.
- **Overview:** a question composer, four quick actions, and only real data: recent conversations, recently updated documents, and documents or reagents needing attention. It shows a first-run state when the library is empty.
- **Ask SmartLab:** a central conversation column with saved history.
  - **Composer:** Enter sends. You can attach one image (answered by the vision pipeline) or one PDF (uploaded with progress, indexed, then queried on its own).
  - **Answer states:** each answer shows one of *supported* / *partially supported* / *no evidence*, plus notices when versions conflict, the cited source is unapproved, verification is needed, or the AI service is down.
  - **Answer actions:** expandable source excerpts, copy, and "Report a problem", which sends the answer to the expert review queue.
- **Evidence panel:** opens only when you click a citation. It is docked at ≥1280 px and a drawer otherwise. It shows the document's type, version, approval status and page, the cited excerpt, and the rendered page with the excerpt highlighted.
- **Documents:** a sortable, filterable table (category, approval status, search) with an upload dialog that shows real progress and indexing status. The detail drawer lets you edit metadata and approval (logged), see other versions, browse pages and extracted text, re-index, and delete.
- **Reagents, Literature, Safety, Activity, Settings:** described in the feature table above. Demo data is labelled as such on every page that shows it.


---

## Lab co-pilot (Ask SmartLab)

Ask SmartLab is a guarded, tool-using co-pilot. It is **decision support, not an authority**. When evidence is weak or a check fails, it says so and refuses instead of guessing.

**Flow.** The model plans, chooses tools and words the checklist. Code does everything that decides whether an answer can be trusted (`backend/app/agents/`):

| Request | Steps (each logged in the trace with `duration_ms`) |
|---|---|
| Preparation ("Prepare 1 L of 50 mM Tris base...") | Screen → Plan → Retrieve → Calculate → Stock check → Compatibility check → Retrieve procedure → Synthesize → Verify |
| SOP question | Screen → Plan → Retrieve → Synthesize → Verify |
| Instrument error | Screen → Plan → Diagnose → Retrieve → Synthesize → Verify |
| Inventory lookup | Screen → Plan → Stock check |

- **Tools** (`agents/tools.py`) are deterministic and read-only. They run on a read-only database connection with validated arguments and a 10 s timeout, with no file access, shell or network. They are SOP search, the preparation calculator (molecular weight from the reagent database; it refuses when the weight is missing), the inventory check (name and synonym matching, explicit unit conversion, expiry), the compatibility check and the error-code lookup (by `upload_id` only).
- **Guardrails** (`guardrails.py`):
  - Every step must cite passages retrieved in this request.
  - Every number must match the cited passage or the calculator output after normalisation ("1 M" = "1M", "100 mL" = "0.1 L", "8,0" = "8.0").
  - Unsupported steps are kept and marked `unsupported: true`.
  - Confidence is computed from retrieval similarity, the share of supported steps and tool outcomes. It never comes from the model's own rating.
  - Retrieved text containing instructions (prompt injection) is quarantined.
- **Status:** **supported** means grounded, in stock and no incompatibility. **caution** means non-blocking issues only: an expiring reagent, an unknown pair, low stock, an unapproved source, or no language model. **refused** means a missing, expired or insufficient reagent, an incompatible pair, a failed tool, an unsupported required step, or confidence below 0.70. A refused checklist is labelled *"Do not follow. Shown for transparency only."*
- **Fail safe:** if the model fails, planning falls back to rules and steps are quoted word for word from the SOPs (status is at most *caution*). There are at most 6 model calls per request, retries included.
- **Wording:** answers say "Supported by uploaded SOP", never "verified" or "safe". The compatibility matrix (`agents/compatibility.py`) is a **limited demo matrix, not expert-reviewed**, and an unlisted pair is *unknown*, never safe.

**API**

| Endpoint | Purpose |
|---|---|
| `POST /api/chat` | Runs the co-pilot. Returns `request_id, response, status, confidence, uncertainty_flag, uncertainty_message, checklist, inventory_status, compatibility, citations, agent_trace`, plus `blockers`, `cautions`, `calculations`, `diagnosis` and `needs_confirmation`. The pre-agent fields (`answer`, `evidence_status`, ...) are still included. Body: `question`, optional `session_id`, `document_ids`, `upload_id`, `error_code` |
| `POST /api/chat/stream` | The same run as Server-Sent Events: one `trace` event per completed step, then `result` (or a generic `error`) |
| `POST /api/agent/uploads` | Instrument photo (PNG/JPEG/WebP, size-checked) → `upload_id` plus the code read from the display, which the user must confirm |
| `GET /api/agent/runs`, `/api/agent/runs/<request_id>` | Read-only audit log: question, tools called (summarised), citations, status, confidence, timestamps |
| `GET /api/agent/info` | Labels the UI shows (matrix label, decision-support note, demo-data flag) |

Chat, stream and upload are rate-limited per client (`SMARTLAB_AGENT_RATE_LIMIT_PER_MIN`, in-process). Client errors are generic; details go to the server log only.

**Organisations.** There is no authentication yet. Every tool and SOP search is filtered by `organization_id`, which is currently `SMARTLAB_DEFAULT_ORG_ID` (default 1) for every request. Look for `TODO(auth)` in `config.py`, `db.py` and `agents/service.py`.

**Demo data.** These are all **demo data**, labelled as such in their titles and in the UI:
- five original sample SOPs written for this demo (`sample_data/sops/*_demo.pdf`: TNE buffer, salt stocks, Tris-glycine-SDS running buffer, bleach decontamination, PHM-200 pH meter error codes);
- seeded stock lots chosen to show each case (in stock, expired, low, expiring, insufficient);
- 23 compounds with molecular weights and synonyms ("Tris" alone is deliberately ambiguous between Tris base and Tris-HCl);
- the demo compatibility matrix;
- troubleshooting entries for an HPLC, a centrifuge and a pH meter.

They are added only to a database that already holds the demo records (`SMARTLAB_SEED_AGENT_DEMO`). Regenerate the PDFs with `python -m app.seed ../sample_data/sops` from `backend/`.

**Evaluation.** `python eval/run_eval.py` (from `backend/`; add `--llm` to use the configured Claude model) runs 21 demo questions on a temporary database. It prints refusal accuracy, citation coverage and guardrail catch rate (corrupted steps marked unsupported, injected instructions caught). These describe the demo set only and are not a benchmark.

---

## Architecture

```
smartlab-ai/
├── backend/                      Flask REST API (Python 3.10+)
│   ├── app/
│   │   ├── __init__.py           App factory: config, CORS, RAG engine, seeding, error handlers
│   │   ├── config.py             Env-driven Config / TestConfig
│   │   ├── db.py                 Schema + helpers; SQLite, or PostgreSQL/Supabase via an sqlite3-compatible adapter
│   │   ├── migrate_sqlite.py     One-off, non-destructive SQLite → PostgreSQL data copy
│   │   ├── security.py           Upload validation pipeline
│   │   ├── guardrails.py         Query screening + vision output sanitiser
│   │   ├── seed.py               Demo SOP PDFs (generated with PyMuPDF) + demo records
│   │   ├── rag/
│   │   │   ├── pdf_extractor.py  PyMuPDF page text, header/footer removal, page-bounded chunks, highlighted page render
│   │   │   ├── embeddings.py     Sentence-Transformers or hashing embedder (auto-fallback)
│   │   │   ├── vector_store.py   FAISS IndexIDMap(FlatIP) or NumPy store, persisted
│   │   │   └── engine.py         Ingest / retrieve / answer / citation validation
│   │   ├── vision/analyzer.py    Claude vision (structured JSON) or heuristics → guardrails → SOP retrieval
│   │   ├── services/             llm.py, inventory.py, troubleshooting.py, literature.py, simulation.py
│   │   └── api/                  One blueprint per area (documents, chat, reagents, vision, ...)
│   ├── tests/                    pytest suite (offline and deterministic; optional PostgreSQL run)
│   ├── requirements.txt          Core dependencies
│   ├── requirements-ml.txt       Optional: sentence-transformers + faiss-cpu
│   └── run.py                    Dev server entry point
└── frontend/                     React 18 + Vite + Tailwind + Recharts + react-markdown/KaTeX
    └── src/
        ├── App.jsx               Shell: sidebar · workspace · citation panel
        ├── context/AppContext.jsx Toasts, theme, document library, citation state
        ├── components/           ui.jsx (Dropzone, Markdown w/ citation chips, Skeleton...), Sidebar, CitationPanel, CommentThread
        ├── views/                One view per module
        └── lib/                  api.js (REST client), chartTheme.js (validated chart palette)
```

### RAG pipeline

1. **Validate** the upload: extension allow-list, magic bytes, size, PDF parse, no encryption, page limit, and no JavaScript/launch/embedded-file content.
2. **Extract** each page with PyMuPDF (`get_text(sort=True)`). Running headers and footers are removed, then the text is split into sentences and headings.
3. **Chunk** by greedy sentence packing (default 700 chars, 120 overlap). Chunks **never cross a page**, which is what makes page-exact citations possible.
4. **Embed** with `all-MiniLM-L6-v2` (if `sentence-transformers` is installed) or the deterministic hashing embedder. Vectors are normalised and stored in FAISS (or NumPy), keyed by the SQLite chunk id.
5. **Retrieve** the top-k chunks by cosine similarity, with a light lexical re-rank so exact error codes and part numbers count.
6. **Gate** on evidence. Chunks below the threshold are not evidence (hashing ≈ 0.12, MiniLM ≈ 0.30). If nothing passes, the reply says so and makes no claims.
7. **Answer.** Claude answers only from numbered `[S#]` sources, or the offline path extracts the best-matching sentences. Markers are renumbered and checked; unknown ids are dropped.
8. **Return** the answer with citations (`document_title`, `page`, verbatim `snippet`, `score`), `evidence_status`, `confidence`, warnings and the guardrail report.

---

## Setup

### Prerequisites
- Python **3.10+** (tested on 3.14)
- Node.js **18+** (tested on 24)

### 1. Backend

```bash
cd smartlab-ai/backend
python -m venv .venv
# Windows:  .venv\Scripts\activate      macOS/Linux:  source .venv/bin/activate
pip install -r requirements.txt
# Optional - dense embeddings + FAISS (downloads a ~90 MB model on first run):
pip install -r requirements-ml.txt

python run.py           # → http://127.0.0.1:5000  (GET /api/health)
```

On first start the database is created in `backend/instance/` and seeded with four demo SOP PDFs, 12 reagents, verified fixes, projects, experiments, datasets and equipment. Seeding only runs against an empty database. Delete `backend/instance/` to reset.

### 2. Frontend

```bash
cd smartlab-ai/frontend
npm install
npm run dev             # → http://localhost:5173  (proxies /api to :5000)
```

Production build: `npm run build` writes to `frontend/dist/`. Serve that folder behind the same origin as the API, or set `VITE_API_BASE` at build time and add the origin to `SMARTLAB_CORS_ORIGINS`.

### 3. Enable Claude (optional)

```bash
export ANTHROPIC_API_KEY=sk-ant-...     # PowerShell: $env:ANTHROPIC_API_KEY="sk-ant-..."
python run.py
```

The health badge in the top bar switches from **Offline mode** to the model name. Requests use `claude-opus-5-5` with adaptive thinking and `effort: medium`. They also enable server-side refusal fallback (`fallbacks: "default"`). Vision responses use a strict JSON schema. Any API failure falls back to the offline path instead of erroring.

### 4. Run the tests

```bash
cd smartlab-ai/backend
python -m pytest            # SQLite, ~30 s, no network or API key needed
```

PostgreSQL integration tests are skipped unless `SMARTLAB_TEST_DATABASE_URL` is set (see [Testing against PostgreSQL](#testing-against-postgresql)).

| Test file | Covers |
|---|---|
| `test_vector_search.py` | Embedder determinism, NumPy + FAISS stores (add/search/filter/persist/replace), page-preserving extraction, footer removal, chunking, retrieval of the right page, index rebuild |
| `test_citations.py` | Every grounded answer carries valid page citations; facts cited from the exact page; hallucinated `[S#]` dropped; uncited LLM output rejected; tampering detected; highlighted page preview |
| `test_uncertainty.py` | Off-topic → `insufficient` with no invented values; empty index; partial evidence flagged; LLM `INSUFFICIENT_EVIDENCE` respected; query guardrails (identification, medical, interlock bypass) |
| `test_vision_guardrails.py` | Identification claims detected and redacted, observations preserved, display text kept verbatim, end-to-end LLM redaction, error display → SOP page + verified fix, heuristic offline mode |
| `test_reagents.py` | Status/expiry logic, filters, SQL-injection-safe sorting, natural-language queries, stock never negative, payload validation, CRUD API |
| `test_file_validation.py` | Path traversal, spoofed extensions, oversized/empty/corrupt/encrypted/JavaScript PDFs, page limit, truncated images, decompression bomb, UTF-8 text |
| `test_troubleshooting_search.py` | Error-code extraction and ranking, symptom matching, unverified entries hidden, unified search |
| `test_experiments_reviews.py` | Checklist progress, reorder, variable log, review roll-up (approve / changes requested), profiles |
| `test_data_collaboration.py` | Dataset sort/filter/stats, CSV import, threaded comments, shared files (forced download), activity feed |
| `test_simulation_literature.py` | Model correctness (½Vmax at Km, ΔCt per 10-fold, cardinal temperature, 4PL midpoint), validation, Europe PMC parsing, offline fallback |
| `test_governance.py` | Document filters/sort/metadata/approval audit, version listing, re-index, conversation history, answer feedback → review queue → resolve, safety endpoints, settings, reagent audit, literature year filter/sort/sample labelling, schema migration of an old database |
| `test_documents_api.py` | Upload → query → delete cycle, duplicate detection, text-less PDF, equipment tour, Claude client request shape / refusal / JSON |
| `test_database_adapter.py` | Engine selection and env-var precedence, URL normalisation and password redaction, SQL translation (placeholders, literals, `LIKE`, `datetime('now')`), PostgreSQL schema, generated ids, row/cursor parity with `sqlite3`, pooled connection cleanup and rollback, SQLite request lifecycle |
| `test_agent_tools.py` | Co-pilot tools: unit conversion, molar and mass-concentration calculations, missing molecular weight refused, "Tris" ambiguity, stock sufficiency with conversion, expired/expiring/missing/incomparable units, organisation scoping, parameterised names, compatibility (incompatible / unknown / no known issue), error-code diagnosis, `upload_id` path-traversal rejection, read-only connection, timeout and exception fail safe |
| `test_agent_guardrails.py` | Number normalisation and mismatch detection, unsupported steps kept and marked, computed confidence, status rules, injection screen; orchestrator with a scripted model: grounded run, number mismatch retried then refused, invented passage id, plan numbers checked against the question, `insufficient_evidence` respected, model failure, call budget, tool timeout, unsafe request, prompt injection in an uploaded PDF |
| `test_agent_api.py` | `/api/chat` contract, SSE trace events then result, generic stream errors, input validation, rate limit, image upload validation and server-generated names, confirm-code flow, audit log, structured chat history, cross-organisation isolation |
| `test_agent_scenarios.py` | Demo-data scenarios: fully supported run, missing / expired / insufficient reagent, incompatible pair, unknown pair (caution, not safe), missing molecular weight, ambiguous compound, mass mismatch, unanswerable question, pH-meter fix with PPE, inventory lookup |
| `test_postgres_integration.py` | Real PostgreSQL: ids, timestamp format, numeric JSON, double precision, case-insensitive search, rollback recovery, pooled connections after errors, upserts, column migration, SQLite → PostgreSQL data migration (requires `SMARTLAB_TEST_DATABASE_URL`) |

---

## Configuration

All settings are environment variables (see `backend/app/config.py` and `.env.example`):

| Variable | Default | Purpose |
|---|---|---|
| `ANTHROPIC_API_KEY` | - | Enables Claude features |
| `SMARTLAB_LLM_MODEL` | `claude-opus-5-5` | Model id |
| `SMARTLAB_LLM_EFFORT` | `medium` | `low` … `max` |
| `SMARTLAB_EMBEDDINGS` | `auto` | `auto` / `sentence-transformers` / `hashing` |
| `SMARTLAB_VECTOR_STORE` | `auto` | `auto` / `faiss` / `numpy` |
| `SMARTLAB_MIN_EVIDENCE_SCORE` | per embedder | Evidence threshold override |
| `SMARTLAB_CHUNK_SIZE` / `_OVERLAP` | `700` / `120` | Chunking |
| `SMARTLAB_MAX_UPLOAD_MB` | `25` | Upload limit |
| `SMARTLAB_LITERATURE_ONLINE` | `true` | Use Europe PMC (false = offline sample corpus) |
| `SMARTLAB_DATA_DIR` | `backend/instance` | SQLite DB, uploads, index |
| `SMARTLAB_DATABASE_URL` | - | PostgreSQL / Supabase URL. When set, used instead of SQLite |
| `DATABASE_URL` | - | Fallback for the above (ignored unless it is a `postgres(ql)://` URL) |
| `SMARTLAB_DB_POOL_MAX` | `5` | Max pooled PostgreSQL connections per server process |
| `SMARTLAB_CORS_ORIGINS` | `http://localhost:5173,...` | Allowed browser origins |
| `SMARTLAB_SEED_DEMO` | `true` | Seed demo data into an empty DB |
| `SMARTLAB_AUTH_REQUIRED` | `true` | Require sign-in for every API route except health and auth |
| `SMARTLAB_SESSION_DAYS` | `14` | Session lifetime |
| `SMARTLAB_COOKIE_SECURE` | `auto` | `true` in production behind HTTPS |
| `SMARTLAB_LOGIN_ATTEMPT_LIMIT` | `10` | Login/reset attempts per 15 min, per client and per email |
| `SMARTLAB_PUBLIC_URL` | `http://localhost:5173` | Base URL used in password-reset links |
| `SMARTLAB_RESET_TOKEN_MINUTES` | `30` | Reset link lifetime |
| `SMARTLAB_SMTP_HOST` / `_PORT` / `_USER` / `_PASSWORD` / `_FROM` / `_STARTTLS` | - | Email for reset links (unset: link is logged) |
| `SMARTLAB_SEED_AGENT_DEMO` | `true` | Add the co-pilot demo SOPs, stock lots and fixes (only to a demo-seeded DB) |
| `SMARTLAB_DEFAULT_ORG_ID` | `1` | Organisation every request is scoped to |
| `SMARTLAB_AGENT_TOOL_TIMEOUT_S` | `10` | Per-tool timeout; a timed-out tool makes the answer fail safe |
| `SMARTLAB_AGENT_TIMEOUT_S` / `_LLM_TIMEOUT_S` | `90` / `60` | Whole-request deadline / one model call |
| `SMARTLAB_AGENT_MAX_LLM_CALLS` | `6` | Model calls per request, retries included |
| `SMARTLAB_AGENT_RATE_LIMIT_PER_MIN` | `20` | Chat, stream and upload requests per minute per client (0 disables) |
| `SMARTLAB_AGENT_UPLOAD_MAX_MB` | `8` | Size limit for co-pilot image uploads |

**Production:** serve with a WSGI server (`waitress-serve --port=5000 --call app:create_app` on Windows, or `gunicorn "app:create_app()"`). Set `SMARTLAB_SECRET_KEY`, serve over HTTPS with `SMARTLAB_COOKIE_SECURE=true`, and configure SMTP for password resets (see [Authentication](#authentication)). For a hosted database, see [Deploying with Supabase](#deploying-with-supabase-postgresql).

## Deploying with Supabase (PostgreSQL)

The backend runs on local SQLite unless `SMARTLAB_DATABASE_URL` (or `DATABASE_URL`) holds a PostgreSQL URL. In that case it connects to PostgreSQL instead. The API and the frontend are the same either way, and `GET /api/health` reports `"database": "sqlite"` or `"postgresql"`. Tables are created automatically on first start. Start-up only ever adds missing tables and columns; it never drops anything.

Pushing to GitHub does **not** move your data. The SQLite file, `.env` and `instance/` are git-ignored on purpose. The Supabase schema is created when the app first connects, and existing local data is copied with the migration command below.

### 1. Get the connection string

In the Supabase dashboard, open **Connect** and copy the URI for the right mode:

| Where the backend runs | Use | Looks like |
|---|---|---|
| A long-running server (VM, Render, Railway, Fly, your laptop) | **Session pooler** (IPv4) | `postgresql://postgres.<ref>:<password>@aws-0-<region>.pooler.supabase.com:5432/postgres` |
| Serverless / many short-lived processes | **Transaction pooler** | same host, port `6543` |
| A host with IPv6 connectivity | Direct connection | `postgresql://postgres:<password>@db.<ref>.supabase.co:5432/postgres` |

The direct connection is IPv6-only unless you buy the IPv4 add-on, and many hosts and home networks are IPv4-only, so the session pooler is the safe default. Append `?sslmode=require`. URL-encode special characters in the password (for example `@` becomes `%40`).

### 2. Configure it (never commit it)

- **Local:** put `SMARTLAB_DATABASE_URL=...` in `smartlab-ai/.env` or `backend/.env`. Both are git-ignored and read at start-up, and real environment variables take precedence. Remove the line to go back to SQLite.
- **Hosting provider:** add `SMARTLAB_DATABASE_URL` as a secret environment variable in its dashboard.

Logs show the database host with the password masked (`postgresql://postgres.<ref>:***@...`).

### 3. Copy existing local data (optional)

Run this **before** the app's first start against Supabase. Otherwise demo seeding fills the tables and the copy refuses to run.

```bash
cd smartlab-ai/backend
# with SMARTLAB_DATABASE_URL set (e.g. in .env)
python -m app.migrate_sqlite --dry-run   # copies inside a transaction, verifies counts, rolls back
python -m app.migrate_sqlite             # copies and commits
```

How the migration behaves:

- It opens the SQLite file read-only.
- It creates the schema if needed.
- It refuses to write if any target table already has rows. It never deletes or overwrites anything.
- It copies every table in foreign-key order in a single transaction, keeping primary keys, NULLs, timestamps, the audit history and comment threads.
- It advances the id sequences past the copied rows.

Use `--sqlite path/to/other.db` to copy a different SQLite file.

Uploaded files are not stored in the database. Copy `backend/instance/uploads/` to the server's upload directory (`SMARTLAB_DATA_DIR/uploads`). The vector index is rebuilt from the database automatically on start-up.

### 4. Run the backend

```bash
pip install -r requirements.txt          # includes psycopg2-binary
gunicorn -w 1 --threads 8 -b 0.0.0.0:$PORT "app:create_app()"   # Linux hosts
# Windows: waitress-serve --port=5000 --threads=8 --call app:create_app
```

Then check `GET /api/health`. It should report `"database": "postgresql"`.

Deployment notes:
- **One process, several threads.** The vector index lives in process memory, so a document uploaded through one worker process is not searchable from another until they restart. Set `SMARTLAB_DB_POOL_MAX` to at least the thread count.
- **Persistent disk for files.** Uploaded PDFs and shared files are written to `SMARTLAB_DATA_DIR`. On hosts with ephemeral disks, mount a persistent volume there. Without one, files are lost on redeploy: answers still work because chunk text is in the database, but page previews and downloads return 410.
- **Demo data.** Set `SMARTLAB_SEED_DEMO=false` if you don't want the demo SOPs and records in a new production database.
- **Lock down Supabase's Data API.** Supabase exposes tables in the `public` schema through its REST API to anyone holding the project's anon key. This backend doesn't use that API, so in the SQL editor run `ALTER TABLE <table> ENABLE ROW LEVEL SECURITY;` for each SmartLab table, or remove `public` from the exposed schemas (Settings → API). The backend connects as the table owner, so RLS does not affect it.

### Testing against PostgreSQL

The default test run uses SQLite only. `TestConfig` ignores `SMARTLAB_DATABASE_URL`, so tests never touch your Supabase database. To run the whole suite plus the PostgreSQL integration tests against a **disposable** database (each test uses its own temporary schema, which is then dropped):

```bash
docker run -d --rm --name smartlab-pg -e POSTGRES_PASSWORD=pw -p 55432:5432 postgres:16-alpine
SMARTLAB_TEST_DATABASE_URL=postgresql://postgres:pw@127.0.0.1:55432/postgres python -m pytest
```

## Upgrading an existing database

New columns (document metadata, reagent category) are added automatically on start-up. Existing documents become *Unreviewed* in category *General*; set their status in Documents. To reload the demo data instead, stop the server and delete `backend/instance/`.

## Authentication

- **Pages:** the landing page is public at `/`; `#/login`, `#/signup`, `#/forgot-password`, `#/reset-password`, `#/privacy`, `#/terms` and `#/contact` are public too. Every app page (`#/overview`, `#/documents`, ...) requires sign-in and redirects to `#/login?next=...`.
- **API:** every `/api` route except `/api/health` and `/api/auth/*` returns `401` without a valid session. Endpoints: `POST /api/auth/signup`, `POST /api/auth/login`, `POST /api/auth/logout`, `GET /api/auth/me`, `POST /api/auth/forgot-password`, `POST /api/auth/reset-password`.
- **Accounts:** the first account created becomes `admin`; later sign-ups are `member`. Each account gets a researcher profile so comments, shared files and experiments are attributed to it.
- **Passwords:** at least 12 characters and not a common or easily guessed password; stored only as salted scrypt hashes (Werkzeug).
- **Sessions:** random 256-bit token in an httpOnly, SameSite=Lax cookie (`smartlab_session`); only its SHA-256 hash is stored server-side. Logging out deletes the session; resetting a password signs out every session.
- **Password reset:** the forgot-password response is identical whether or not the account exists. Links are single-use, expire after 30 minutes, and only the newest link works. Without SMTP settings the link is written to the backend log (development).
- **Abuse protection:** login, sign-up and reset attempts are rate-limited; state-changing requests from origins outside `SMARTLAB_CORS_ORIGINS` are rejected.
- **Tests:** `tests/test_auth.py` covers the above. The other test modules run with `AUTH_REQUIRED` off (`TestConfig`) so they exercise features directly.

## Known limitations
- Accounts have a role (admin or member), but feature permissions are not role-specific yet: any signed-in user can approve documents and edit records.
- Conflict detection covers *versions of the same document* (shared document code). Contradictions between different documents are not detected.
- Scanned (image-only) PDFs are rejected with a clear message; run OCR first.
- Offline image analysis is heuristic (colours, brightness, indicator lights). Reading text off a display needs the Claude vision path, or the user can type the code into the note.
- Collaboration updates use 5 s polling, not WebSockets.
- Login rate limits are kept in process memory; with several server processes, put a shared limiter (or the reverse proxy) in front.
- Co-pilot:
  - The compatibility matrix is a small demo table, not expert-reviewed. Unknown pairs are only flagged.
  - The calculator gives the mass of the pure compound for solids. It does not handle dilution from liquid stocks, hydrate conversion or purity.
  - The number check confirms that values appear in the cited passage, not that they are used in the right context.
  - The injection screen is pattern-based.
  - The rate limiter is per server process.
  - Without a model, steps are quoted verbatim from the SOPs and the status is at most *caution*.
