import urllib.request
import json
import psycopg2
import os

print("=================================================================")
print("             SMARTLAB AI - FULL STACK FINAL AUDIT                ")
print("=================================================================")

# 1. CLOUD DATABASE (SUPABASE POSTGRESQL)
print("\n[1/4] TESTING SUPABASE POSTGRESQL CLOUD DATABASE...")
supabase_url = os.getenv("SMARTLAB_DATABASE_URL")
if not supabase_url:
    import sys
    sys.path.insert(0, ".")
    from app.config import Config
    supabase_url = Config.DATABASE_URL

assert supabase_url, "SMARTLAB_DATABASE_URL is not set!"
conn = psycopg2.connect(supabase_url, connect_timeout=5)
cur = conn.cursor()
cur.execute("SELECT version();")
pg_version = cur.fetchone()[0]
print(f"  [OK] Connected to Cloud Engine: {pg_version[:40]}...")

cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public';")
tables = [r[0] for r in cur.fetchall()]
print(f"  [OK] Found {len(tables)} tables in Supabase public schema.")

for tbl in ["documents", "chunks", "reagents", "troubleshooting", "experiments", "equipment", "settings"]:
    cur.execute(f"SELECT COUNT(*) FROM {tbl};")
    cnt = cur.fetchone()[0]
    print(f"       * {tbl:<16}: {cnt} rows")
conn.close()

# 2. BACKEND API (FLASK @ http://127.0.0.1:5000)
print("\n[2/4] TESTING BACKEND API DIRECTLY (http://127.0.0.1:5000)...")
req = urllib.request.Request("http://127.0.0.1:5000/api/health")
with urllib.request.urlopen(req, timeout=5) as res:
    health = json.loads(res.read().decode())
    assert health.get("status") == "ok"
    assert health.get("database") == "postgresql"
    print(f"  [OK] GET /api/health -> HTTP {res.status}")
    print(f"       * Status: {health.get('status')}")
    print(f"       * Active Database Engine: {health.get('database')}")
    print(f"       * Vector Store: {health.get('vector_store')} ({health.get('indexed_chunks')} chunks)")

# 3. FRONTEND DEV SERVER & VITE REVERSE PROXY (http://localhost:5173)
print("\n[3/4] TESTING FRONTEND REVERSE PROXY TO SUPABASE (http://localhost:5173)...")
routes = [
    ("/api/health", "GET"),
    ("/api/documents", "GET"),
    ("/api/reagents", "GET"),
    ("/api/reagents/summary", "GET"),
    ("/api/safety", "GET"),
    ("/api/settings", "GET"),
    ("/api/search/unified?q=hplc", "GET"),
    ("/api/troubleshooting", "GET"),
    ("/api/experiments", "GET"),
    ("/api/datasets", "GET"),
    ("/api/projects", "GET"),
    ("/api/chat/sessions", "GET"),
]
for path, method in routes:
    url = f"http://localhost:5173{path}"
    req = urllib.request.Request(url, method=method)
    with urllib.request.urlopen(req, timeout=5) as res:
        data = json.loads(res.read().decode())
        item_count = len(data) if isinstance(data, list) else len(data.keys())
        print(f"  [OK] Vite -> Backend -> Supabase: {method} {path} (HTTP {res.status}, {item_count} items)")

# 4. FRONTEND UI HOME PAGE
print("\n[4/4] TESTING FRONTEND WEB PAGE DELIVERY...")
with urllib.request.urlopen("http://localhost:5173/", timeout=5) as res:
    html = res.read().decode()
    assert "<title>" in html or "id=\"root\"" in html
    print(f"  [OK] GET http://localhost:5173/ -> HTTP {res.status} (React HTML Bundle Delivered)")

print("\n=================================================================")
print(" >>> ALL FRONTEND, BACKEND, AND SUPABASE CONNECTIONS VERIFIED <<< ")
print("=================================================================")
