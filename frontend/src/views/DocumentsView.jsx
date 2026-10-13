import { useEffect, useMemo, useRef, useState } from "react";
import {
  ArrowDown, ArrowUp, ChevronLeft, ChevronRight, Download, FileText, MessageSquareText, MoreHorizontal, RefreshCw, Search,
  SlidersHorizontal, Trash2, UploadCloud,
} from "lucide-react";
import { useApp } from "../context/AppContext";
import { api } from "../lib/api";
import { docKind, formatBytes, formatDate, formatDateTime, plural } from "../lib/format";
import { setPendingQuestion } from "../lib/pending";
import { navigate } from "../lib/router";
import {
  ApprovalBadge, Badge, Dialog, Drawer, DropZone, EmptyState, ErrorState, Field, Notice, Page, PageHeader, ProgressBar,
  SkeletonRows, Spinner, useAsync, useDebounced,
} from "../components/ui";
import { Floating, MenuButton, useDismiss } from "../components/Popover";

const STATUS_FILTERS = [
  { id: "", label: "All statuses" }, { id: "approved", label: "Approved" }, { id: "review", label: "Needs review" },
  { id: "pending", label: "Pending" }, { id: "unreviewed", label: "Unreviewed" }, { id: "outdated", label: "Outdated" },
];
const EMPTY_META = { title: "", doc_code: "", version: "", category: "", owner: "", doc_type: "SOP" };

function MetadataFields({ value, onChange, categories, includeStatus }) {
  const set = (k) => (e) => onChange({ ...value, [k]: e.target.value });
  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
      <Field label="Title" className="sm:col-span-2" hint={includeStatus ? undefined : "Leave blank to use the PDF's own title."}>
        {(id) => <input id={id} className="input" value={value.title} onChange={set("title")} maxLength={200} />}
      </Field>
      <Field label="Document code" hint="Shared by all versions, e.g. SOP-HPLC-004">
        {(id) => <input id={id} className="input" value={value.doc_code ?? ""} onChange={set("doc_code")} maxLength={120} />}
      </Field>
      <Field label="Version">{(id) => <input id={id} className="input" value={value.version ?? ""} onChange={set("version")} maxLength={40} placeholder="e.g. 2.1" />}</Field>
      <Field label="Category">
        {(id) => (
          <>
            <input id={id} className="input" list="doc-categories" value={value.category ?? ""} onChange={set("category")} placeholder="e.g. Safety, Instrument" />
            <datalist id="doc-categories">{categories.map((c) => <option key={c} value={c} />)}</datalist>
          </>
        )}
      </Field>
      <Field label="Type">
        {(id) => (
          <select id={id} className="input" value={value.doc_type} onChange={set("doc_type")}>
            {["SOP", "Manual", "Safety data sheet", "Troubleshooting guide", "Policy", "Paper", "Other"].map((t) => <option key={t}>{t}</option>)}
          </select>
        )}
      </Field>
      <Field label="Owner">{(id) => <input id={id} className="input" value={value.owner ?? ""} onChange={set("owner")} maxLength={120} />}</Field>
      {includeStatus && (
        <Field label="Approval status" hint="Changes are recorded in the document history.">
          {(id) => (
            <select id={id} className="input" value={value.approval_status} onChange={set("approval_status")}>
              <option value="approved">Approved</option><option value="pending">Pending review</option>
              <option value="unreviewed">Unreviewed</option><option value="outdated">Outdated</option>
            </select>
          )}
        </Field>
      )}
    </div>
  );
}

function UploadDialog({ open, onClose, onUploaded, categories, maxMB }) {
  const { toast } = useApp();
  const [file, setFile] = useState(null);
  const [meta, setMeta] = useState(EMPTY_META);
  const [state, setState] = useState(null); // {phase, progress} | {phase:"error", message}

  useEffect(() => { if (open) { setFile(null); setMeta(EMPTY_META); setState(null); } }, [open]);
  const working = state?.phase === "uploading" || state?.phase === "processing";

  const start = async () => {
    setState({ phase: "uploading", progress: 0 });
    try {
      const doc = await api.uploadDocument(file, meta, {
        onProgress: (p) => setState(p >= 1 ? { phase: "processing" } : { phase: "uploading", progress: p }),
      });
      toast(`"${doc.title}" indexed: ${plural(doc.page_count, "page")}, ${plural(doc.chunk_count, "passage")}. Marked Unreviewed until approved.`, "success");
      onUploaded(doc);
    } catch (err) {
      setState({ phase: "error", message: err.message, existing: err.status === 409 ? err.data?.document : null });
    }
  };

  return (
    <Dialog open={open} onClose={() => !working && onClose()} title="Upload document" size="max-w-xl"
      description="Text-based PDFs only. Scanned PDFs need OCR before upload."
      footer={<>
        <button className="btn-secondary" onClick={onClose} disabled={working}>Cancel</button>
        <button className="btn-primary" disabled={!file || working} onClick={start}>
          {working && <Spinner />}{state?.phase === "error" ? "Retry upload" : "Upload and index"}
        </button>
      </>}>
      <div className="space-y-4">
        {file ? (
          <div className="flex items-center gap-3 rounded-lg border border-line bg-canvas p-3">
            <FileText className="h-5 w-5 text-muted" aria-hidden="true" />
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium">{file.name}</p>
              <p className="meta">{formatBytes(file.size)}</p>
            </div>
            {!working && <button className="btn-ghost btn-sm" onClick={() => { setFile(null); setState(null); }}>Change</button>}
          </div>
        ) : (
          <DropZone accept=".pdf" maxMB={maxMB} onFiles={([f]) => setFile(f)} label="Drop a PDF here or choose a file" hint={`PDF up to ${maxMB} MB`} />
        )}
        {state?.phase === "uploading" && <div className="space-y-1"><ProgressBar value={state.progress} label="Upload progress" /><p className="meta">Uploading {Math.round(state.progress * 100)}%</p></div>}
        {state?.phase === "processing" && <p className="flex items-center gap-2 text-sm text-muted"><Spinner /> Validating, extracting pages and indexing passages...</p>}
        {state?.phase === "error" && (
          <Notice tone="critical" title="Upload failed"
            action={state.existing && <button className="btn-secondary btn-sm" onClick={() => { onClose(); navigate(`documents/${state.existing.id}`); }}>Open existing document</button>}>
            {state.message}
          </Notice>
        )}
        <MetadataFields value={meta} onChange={setMeta} categories={categories} />
        <p className="meta">New documents start as <strong>Unreviewed</strong>. Answers that cite them are flagged until they are approved.</p>
      </div>
    </Dialog>
  );
}

function DocumentDrawer({ id, page, onClose, onChanged, categories }) {
  const { toast, confirm, openEvidence } = useApp();
  const doc = useAsync(() => api.document(id), [id]);
  const [form, setForm] = useState(null);
  const [saving, setSaving] = useState(false);
  const [reindexing, setReindexing] = useState(false);
  const [selectedPage, setSelectedPage] = useState(page ?? null);
  const pageText = useAsync(() => (selectedPage ? api.pageText(id, selectedPage) : Promise.resolve(null)), [id, selectedPage]);

  useEffect(() => {
    if (doc.data) setForm({ ...EMPTY_META, ...Object.fromEntries(Object.entries(doc.data).map(([k, v]) => [k, v ?? ""])) });
  }, [doc.data]);

  const d = doc.data;
  const dirty = d && form && ["title", "doc_code", "version", "category", "owner", "doc_type", "approval_status"].some((k) => (d[k] ?? "") !== form[k]);

  const save = async () => {
    if (form.approval_status !== d.approval_status && form.approval_status === "approved" &&
      !(await confirm({ title: "Approve this document?", message: `"${form.title}" will be treated as a current approved source in answers. This change is recorded in the document history.`, confirmLabel: "Approve" }))) return;
    setSaving(true);
    try {
      const payload = Object.fromEntries(["title", "doc_code", "version", "category", "owner", "doc_type", "approval_status"].map((k) => [k, form[k]]));
      await api.updateDocument(id, payload);
      toast("Document details saved.", "success");
      doc.reload();
      onChanged();
    } catch (err) { toast(err.message, "error"); } finally { setSaving(false); }
  };

  const reindex = async () => {
    setReindexing(true);
    try {
      const r = await api.reindexDocument(id);
      toast(`Re-indexed: ${r.chunk_count} passages from ${r.page_count} pages.`, "success");
      doc.reload();
      onChanged();
    } catch (err) { toast(err.message, "error"); } finally { setReindexing(false); }
  };

  const remove = async () => {
    if (!(await confirm({ title: "Remove document?", message: `"${d.title}" will be deleted and no longer used for answers. Existing conversations keep their text but its citations will no longer open.`, confirmLabel: "Remove", danger: true }))) return;
    try {
      await api.deleteDocument(id);
      toast("Document removed.", "success");
      onChanged();
      onClose();
    } catch (err) { toast(err.message, "error"); }
  };

  return (
    <Drawer open onClose={onClose} width="sm:w-[34rem]" title={d?.title ?? "Document"}
      subtitle={d && <div className="flex flex-wrap items-center gap-1.5"><ApprovalBadge status={d.approval_status} />{d.version && <Badge>v{d.version}</Badge>}<Badge>{d.doc_type}</Badge></div>}
      footer={d && form && <>
        <button className="btn-ghost mr-auto text-critical hover:bg-critical-soft hover:text-critical" onClick={remove}><Trash2 className="h-4 w-4" /> Remove</button>
        <button className="btn-secondary" onClick={() => setForm({ ...EMPTY_META, ...Object.fromEntries(Object.entries(d).map(([k, v]) => [k, v ?? ""])) })} disabled={!dirty || saving}>Discard</button>
        <button className="btn-primary" onClick={save} disabled={!dirty || saving}>{saving && <Spinner />} Save changes</button>
      </>}>
      {doc.loading && !d ? <SkeletonRows rows={6} /> : doc.error ? <ErrorState error={doc.error} onRetry={doc.reload} /> : d && form && (
        <div className="space-y-6">
          {d.approval_status === "outdated" && <Notice tone="warning" title="Outdated version">This copy is kept for reference. Answers prefer the approved version when one exists.</Notice>}
          {d.other_versions.length > 0 && (
            <section>
              <h3 className="eyebrow mb-2">Other versions of {d.doc_code}</h3>
              <ul className="divide-y divide-line rounded-lg border border-line">
                {d.other_versions.map((v) => (
                  <li key={v.id}>
                    <a href={`#/documents/${v.id}`} className="flex items-center gap-2 px-3 py-2 text-sm hover:bg-subtle">
                      <span className="flex-1">Version {v.version ?? "unversioned"}</span><ApprovalBadge status={v.approval_status} />
                    </a>
                  </li>
                ))}
              </ul>
            </section>
          )}
          <section>
            <h3 className="eyebrow mb-2">Details</h3>
            <MetadataFields value={form} onChange={setForm} categories={categories} includeStatus />
            <dl className="mt-3 grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
              <dt className="text-muted">File</dt><dd className="truncate">{d.original_name} ({formatBytes(d.size_bytes)})</dd>
              <dt className="text-muted">Uploaded</dt><dd>{formatDateTime(d.uploaded_at)}</dd>
              <dt className="text-muted">Last reviewed</dt><dd>{d.reviewed_at ? formatDateTime(d.reviewed_at) : "Not recorded"}</dd>
              <dt className="text-muted">Indexed</dt><dd>{plural(d.page_count, "page")} · {plural(d.chunk_count, "passage")}</dd>
            </dl>
          </section>
          <section>
            <div className="mb-2 flex items-center justify-between">
              <h3 className="eyebrow">Pages</h3>
              <div className="flex gap-1">
                <button className="btn-ghost btn-sm" onClick={() => { setPendingQuestion("", null, { scope: { id, title: d.title } }); navigate("ask"); }}
                  title="Ask questions answered only from this document"><MessageSquareText className="h-3.5 w-3.5" /> Ask this document</button>
                <button className="btn-ghost btn-sm" onClick={reindex} disabled={reindexing}>{reindexing ? <Spinner className="h-3.5 w-3.5" /> : <RefreshCw className="h-3.5 w-3.5" />} Re-index</button>
                <a className="btn-ghost btn-sm" href={api.documentFileUrl(id)} target="_blank" rel="noreferrer"><Download className="h-3.5 w-3.5" /> PDF</a>
              </div>
            </div>
            <div className="flex flex-wrap gap-1">
              {d.pages.map((p) => (
                <button key={p.page} onClick={() => setSelectedPage(p.page)} aria-pressed={selectedPage === p.page}
                  className={`h-8 min-w-[2rem] rounded-md border px-2 text-xs tabular-nums ${selectedPage === p.page ? "border-accent bg-accent text-white" : "border-line hover:bg-subtle"}`}>
                  {p.page}
                </button>
              ))}
            </div>
            {selectedPage && (
              <div className="mt-3 rounded-lg border border-line">
                <div className="flex items-center justify-between border-b border-line px-3 py-2">
                  <p className="text-xs font-medium">Extracted text · page {selectedPage}</p>
                  <button className="link text-xs" onClick={() => openEvidence({ document_id: id, document_title: d.title, page: selectedPage, snippet: "",
                    version: d.version, approval_status: d.approval_status, doc_type: d.doc_type, category: d.category })}>View page</button>
                </div>
                <div className="max-h-64 space-y-2 overflow-y-auto px-3 py-2 text-sm leading-6">
                  {pageText.loading ? <SkeletonRows rows={3} className="h-4" /> : pageText.data?.chunks.map((c) => <p key={c.id} className="whitespace-pre-line">{c.text}</p>)}
                </div>
              </div>
            )}
          </section>
          {d.history.length > 0 && (
            <section>
              <h3 className="eyebrow mb-2">History</h3>
              <ol className="space-y-1.5 text-xs">
                {d.history.map((h, i) => (
                  <li key={i} className="flex gap-2"><span className="w-32 shrink-0 text-muted">{formatDateTime(h.created_at)}</span><span>{h.summary}{h.actor && <span className="text-muted"> · {h.actor}</span>}</span></li>
                ))}
              </ol>
            </section>
          )}
        </div>
      )}
    </Drawer>
  );
}

const KIND_TABS = [
  { id: "all", label: "All" }, { id: "SOP", label: "SOPs" }, { id: "Manual", label: "Manuals" },
  { id: "Safety", label: "Safety" }, { id: "Other", label: "Other" },
];
const SORTS = {
  title: (d) => d.title.toLowerCase(),
  kind: (d) => docKind(d),
  uploaded_at: (d) => d.uploaded_at ?? "",
  size_bytes: (d) => d.size_bytes ?? 0,
};
const PAGE_SIZE = 10;

function SortHeader({ id, label, sort, onSort, className = "" }) {
  const active = sort.key === id;
  return (
    <th className={className} aria-sort={active ? (sort.order === "asc" ? "ascending" : "descending") : "none"}>
      <button className="inline-flex items-center gap-1 rounded hover:text-ink" onClick={() => onSort(id)}>
        {label}{active && (sort.order === "asc" ? <ArrowUp className="h-3 w-3" aria-hidden="true" /> : <ArrowDown className="h-3 w-3" aria-hidden="true" />)}
      </button>
    </th>
  );
}

function FilterButton({ category, setCategory, status, setStatus, categories }) {
  const [open, setOpen] = useState(false);
  const btnRef = useRef(null);
  const panelRef = useRef(null);
  useDismiss(open, ({ restoreFocus }) => { setOpen(false); if (restoreFocus) btnRef.current?.focus(); }, [btnRef, panelRef]);
  const count = (category ? 1 : 0) + (status ? 1 : 0);
  return (
    <>
      <button ref={btnRef} type="button" className="pill h-9" aria-haspopup="dialog" aria-expanded={open} onClick={() => setOpen((o) => !o)}>
        <SlidersHorizontal aria-hidden="true" /> Filter
        {count > 0 && <span className="flex h-4 min-w-4 items-center justify-center rounded-full bg-accent px-1 text-2xs font-semibold text-white">{count}</span>}
      </button>
      <Floating anchorRef={btnRef} panelRef={panelRef} open={open} placement="bottom-end" className="w-64 p-3" role="dialog" aria-label="Filter documents">
        <div className="space-y-3">
          <Field label="Category">
            {(id) => (
              <select id={id} className="input" value={category} onChange={(e) => setCategory(e.target.value)}>
                <option value="">All categories</option>{categories.map((c) => <option key={c}>{c}</option>)}
              </select>
            )}
          </Field>
          <Field label="Approval status">
            {(id) => (
              <select id={id} className="input" value={status} onChange={(e) => setStatus(e.target.value)}>
                {STATUS_FILTERS.map((x) => <option key={x.id} value={x.id}>{x.label}</option>)}
              </select>
            )}
          </Field>
          {count > 0 && <button type="button" className="link text-xs" onClick={() => { setCategory(""); setStatus(""); }}>Reset filters</button>}
        </div>
      </Floating>
    </>
  );
}

function RowMenu({ doc, onReindex, onRemove }) {
  return (
    <MenuButton label={`Actions for ${doc.title}`} placement="bottom-end" width="w-48"
      items={[
        { id: "open", label: "Open details", icon: FileText },
        { id: "ask", label: "Ask this document", icon: MessageSquareText },
        { id: "pdf", label: "Download PDF", icon: Download },
        { id: "reindex", label: "Re-index", icon: RefreshCw },
        { id: "div", divider: true },
        { id: "remove", label: "Remove", icon: Trash2 },
      ]}
      onSelect={(id) => {
        if (id === "open") navigate(`documents/${doc.id}`);
        if (id === "ask") { setPendingQuestion("", null, { scope: { id: doc.id, title: doc.title } }); navigate("ask"); }
        if (id === "pdf") window.open(api.documentFileUrl(doc.id), "_blank", "noopener");
        if (id === "reindex") onReindex(doc);
        if (id === "remove") onRemove([doc]);
      }}
      renderButton={({ ref, props }) => (
        <button ref={ref} type="button" className="btn-ghost btn-icon h-8 w-8" {...props}>
          <MoreHorizontal className="h-4 w-4" aria-hidden="true" />
        </button>
      )} />
  );
}

export default function DocumentsView({ route }) {
  const { health, toast, confirm } = useApp();
  const openId = route.path[1] ? Number(route.path[1]) : null;
  const [q, setQ] = useState("");
  const [category, setCategory] = useState("");
  const [status, setStatus] = useState(route.query.status ?? "");
  const [kind, setKind] = useState("all");
  const [sort, setSort] = useState({ key: "uploaded_at", order: "desc" });
  const [page, setPage] = useState(1);
  const [selected, setSelected] = useState(() => new Set());
  const [uploadOpen, setUploadOpen] = useState(route.query.upload === "1");
  const search = useDebounced(q);

  const facets = useAsync(() => api.documentFacets(), []);
  const settings = useAsync(() => api.settings(), []);
  const list = useAsync(() => api.documents({ q: search, category, status: status === "review" ? "" : status }), [search, category, status]);

  useEffect(() => { if (route.query.status !== undefined) setStatus(route.query.status); }, [route.query.status]);
  useEffect(() => { if (route.query.upload === "1") setUploadOpen(true); }, [route.query.upload]);
  useEffect(() => { setPage(1); }, [search, category, status, kind, sort]);

  const base = useMemo(() => {
    const all = list.data ?? [];
    return status === "review" ? all.filter((d) => d.approval_status === "pending" || d.approval_status === "unreviewed") : all;
  }, [list.data, status]);
  const counts = useMemo(() => {
    const c = { all: base.length, SOP: 0, Manual: 0, Safety: 0, Other: 0 };
    base.forEach((d) => { c[docKind(d)] += 1; });
    return c;
  }, [base]);
  const rows = useMemo(() => {
    const key = SORTS[sort.key];
    const dir = sort.order === "asc" ? 1 : -1;
    return base.filter((d) => kind === "all" || docKind(d) === kind)
      .sort((a, b) => (key(a) < key(b) ? -dir : key(a) > key(b) ? dir : 0));
  }, [base, kind, sort]);
  const pages = Math.max(1, Math.ceil(rows.length / PAGE_SIZE));
  const pageRows = rows.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);
  const filtered = Boolean(search || category || status || kind !== "all");
  const clear = () => { setQ(""); setCategory(""); setStatus(""); setKind("all"); };
  const toggleSort = (key) => setSort((s) => ({ key, order: s.key === key && s.order === "asc" ? "desc" : "asc" }));
  const reload = () => { list.reload(); facets.reload(); };

  const allOnPage = pageRows.length > 0 && pageRows.every((d) => selected.has(d.id));
  const toggleAll = () => setSelected((sel) => {
    const next = new Set(sel);
    pageRows.forEach((d) => (allOnPage ? next.delete(d.id) : next.add(d.id)));
    return next;
  });
  const toggleOne = (id) => setSelected((sel) => {
    const next = new Set(sel);
    if (next.has(id)) next.delete(id); else next.add(id);
    return next;
  });

  const reindex = async (doc) => {
    try {
      const r = await api.reindexDocument(doc.id);
      toast(`Re-indexed "${doc.title}": ${r.chunk_count} passages from ${r.page_count} pages.`, "success");
      reload();
    } catch (err) { toast(err.message, "error"); }
  };
  const remove = async (docs) => {
    const label = docs.length === 1 ? `"${docs[0].title}"` : plural(docs.length, "document");
    if (!(await confirm({
      title: docs.length === 1 ? "Remove document?" : `Remove ${docs.length} documents?`,
      message: `${label} will be deleted and no longer used for answers. Existing conversations keep their text but their citations will no longer open.`,
      confirmLabel: "Remove", danger: true,
    }))) return;
    let removed = 0;
    for (const d of docs) {
      try { await api.deleteDocument(d.id); removed += 1; } catch (err) { toast(`Could not remove "${d.title}": ${err.message}`, "error"); }
    }
    if (removed) toast(`${plural(removed, "document")} removed.`, "success");
    setSelected(new Set());
    reload();
  };

  return (
    <Page width="max-w-7xl">
      <PageHeader title="Documents" description="SOPs, manuals and safety documents that answers are drawn from. Only approved versions are treated as current."
        actions={<button className="btn-primary" onClick={() => setUploadOpen(true)}><UploadCloud className="h-4 w-4" aria-hidden="true" /> Upload document</button>} />
      {settings.data?.demo_data.documents && (
        <Notice tone="info" title="Demo documents" className="mb-4">The sample SOPs were generated for demonstration and are not real laboratory procedures. Remove them before using SmartLab with real documents.</Notice>
      )}

      <div role="tablist" aria-label="Document type" className="mb-4 flex gap-5 overflow-x-auto border-b border-line">
        {KIND_TABS.map((t) => (
          <button key={t.id} role="tab" aria-selected={kind === t.id} className="tab-u shrink-0" onClick={() => setKind(t.id)}>
            {t.label}<span className="ml-1.5 text-xs tabular-nums text-muted">{counts[t.id]}</span>
          </button>
        ))}
      </div>

      <div className="mb-3 flex flex-wrap items-center gap-2">
        <div className="relative w-full sm:w-80">
          <Search className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-faint" aria-hidden="true" />
          <input className="input pl-9" value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search title, code, owner or file name" aria-label="Search documents" />
        </div>
        <FilterButton category={category} setCategory={setCategory} status={status} setStatus={setStatus} categories={facets.data?.categories ?? []} />
        {filtered && <button className="btn-ghost btn-sm" onClick={clear}>Clear</button>}
        <div className="flex-1" />
        {selected.size > 0 ? (
          <div className="flex items-center gap-2 text-sm">
            <span className="text-muted">{selected.size} selected</span>
            <button className="pill h-8 text-critical" onClick={() => remove(rows.filter((d) => selected.has(d.id)))}><Trash2 aria-hidden="true" /> Remove</button>
            <button className="btn-ghost btn-sm" onClick={() => setSelected(new Set())}>Clear selection</button>
          </div>
        ) : <span className="text-xs text-muted">{plural(rows.length, "document")}</span>}
      </div>

      <div className="card overflow-hidden">
        {list.error ? <ErrorState error={list.error} onRetry={list.reload} /> : list.loading && !list.data ? <div className="p-4"><SkeletonRows rows={5} /></div> : rows.length === 0 ? (
          filtered ? <EmptyState icon={Search} title="No documents match" action={<button className="btn-secondary btn-sm" onClick={clear}>Clear filters</button>} />
            : <EmptyState icon={FileText} title="No documents yet" action={<button className="btn-primary" onClick={() => setUploadOpen(true)}>Upload a PDF</button>}>Upload SOPs, manuals and safety documents to start asking questions.</EmptyState>
        ) : (
          <div className="overflow-x-auto">
            <table className="table min-w-[44rem]">
              <thead>
                <tr>
                  <th className="w-10"><input type="checkbox" className="h-4 w-4 accent-accent" checked={allOnPage} onChange={toggleAll} aria-label="Select all documents on this page" /></th>
                  <SortHeader id="title" label="Name" sort={sort} onSort={toggleSort} />
                  <SortHeader id="kind" label="Type" sort={sort} onSort={toggleSort} />
                  <SortHeader id="uploaded_at" label="Date added" sort={sort} onSort={toggleSort} />
                  <SortHeader id="size_bytes" label="Size" sort={sort} onSort={toggleSort} className="text-right" />
                  <th className="w-12"><span className="sr-only">Actions</span></th>
                </tr>
              </thead>
              <tbody>
                {pageRows.map((d) => (
                  <tr key={d.id} className={`row-link ${selected.has(d.id) ? "bg-accent-soft/40" : ""}`} onClick={() => navigate(`documents/${d.id}`)}>
                    <td onClick={(e) => e.stopPropagation()}>
                      <input type="checkbox" className="h-4 w-4 accent-accent" checked={selected.has(d.id)} onChange={() => toggleOne(d.id)} aria-label={`Select ${d.title}`} />
                    </td>
                    <td className="max-w-[26rem]">
                      <div className="flex items-start gap-2.5">
                        <span className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-subtle"><FileText className="h-4 w-4 text-muted" strokeWidth={1.6} aria-hidden="true" /></span>
                        <div className="min-w-0">
                          <a href={`#/documents/${d.id}`} className="block truncate font-medium text-ink hover:text-accent-strong" onClick={(e) => e.stopPropagation()}>{d.title}</a>
                          <div className="mt-0.5 flex flex-wrap items-center gap-1.5 text-xs text-muted">
                            {d.version && <span>v{d.version}</span>}{d.category && <span>· {d.category}</span>}<ApprovalBadge status={d.approval_status} />
                          </div>
                        </div>
                      </div>
                    </td>
                    <td><span className="type-chip">{docKind(d)}</span></td>
                    <td className="whitespace-nowrap text-muted">{formatDate(d.uploaded_at)}</td>
                    <td className="whitespace-nowrap text-right tabular-nums text-muted">{d.size_bytes != null ? formatBytes(d.size_bytes) : "-"}</td>
                    <td className="text-right" onClick={(e) => e.stopPropagation()}><RowMenu doc={d} onReindex={reindex} onRemove={remove} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {rows.length > PAGE_SIZE && (
          <nav aria-label="Pagination" className="flex items-center justify-between gap-2 border-t border-line px-3 py-2.5 text-sm">
            <span className="text-xs text-muted">{(page - 1) * PAGE_SIZE + 1}–{Math.min(page * PAGE_SIZE, rows.length)} of {rows.length}</span>
            <div className="flex items-center gap-1">
              <button className="btn-ghost btn-icon h-8 w-8" disabled={page === 1} onClick={() => setPage((p) => p - 1)} aria-label="Previous page"><ChevronLeft className="h-4 w-4" /></button>
              {Array.from({ length: pages }, (_, i) => i + 1).map((n) => (
                <button key={n} onClick={() => setPage(n)} aria-current={n === page ? "page" : undefined}
                  className={`h-8 min-w-8 rounded-lg px-2 text-sm tabular-nums ${n === page ? "bg-accent font-medium text-white" : "text-muted hover:bg-subtle hover:text-ink"}`}>{n}</button>
              ))}
              <button className="btn-ghost btn-icon h-8 w-8" disabled={page === pages} onClick={() => setPage((p) => p + 1)} aria-label="Next page"><ChevronRight className="h-4 w-4" /></button>
            </div>
          </nav>
        )}
      </div>

      <UploadDialog open={uploadOpen} onClose={() => { setUploadOpen(false); if (route.query.upload) navigate("documents", { replace: true }); }}
        categories={facets.data?.categories ?? []} maxMB={health?.max_upload_mb ?? 25}
        onUploaded={(doc) => { setUploadOpen(false); reload(); navigate(`documents/${doc.id}`); }} />
      {openId && <DocumentDrawer key={openId} id={openId} page={route.query.page ? Number(route.query.page) : null}
        categories={facets.data?.categories ?? []} onChanged={reload} onClose={() => navigate("documents")} />}
    </Page>
  );
}
