"""Copy an existing SmartLab SQLite database into PostgreSQL (e.g. Supabase).

Usage (from ``backend/``, with SMARTLAB_DATABASE_URL set to the target database)::

    python -m app.migrate_sqlite --dry-run          # copy inside a transaction, verify, roll back
    python -m app.migrate_sqlite                    # copy and commit

Safety rules:

* The SQLite file is opened read-only and never modified.
* Nothing in PostgreSQL is dropped, truncated or overwritten. The schema is created with
  ``CREATE TABLE IF NOT EXISTS`` and the copy aborts if any target table already has rows
  (for example because the app already started against the database and seeded demo data).
* Everything runs in one transaction: either every row is copied or nothing is.
* Primary keys are preserved, so foreign keys and the vector index (keyed by chunk id) stay valid;
  identity sequences are then advanced past the copied ids.

Uploaded files (``instance/uploads``) live on disk, not in the database; copy that directory to
the server's SMARTLAB_UPLOAD_DIR separately. The vector index is rebuilt automatically on start-up.
"""
from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

from .config import Config, redact_url, resolve_database
from .db import TABLES, PgConnection, connect, init_schema, is_postgres

SELF_REFERENCES = {"comments": "parent_id"}  # inserted without the reference, then patched


class MigrationError(RuntimeError):
    pass


def _open_sqlite_readonly(path: Path) -> sqlite3.Connection:
    if not path.is_file():
        raise MigrationError(f"SQLite database not found: {path}")
    conn = sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _source_columns(src: sqlite3.Connection, table: str) -> list[str]:
    return [r[1] for r in src.execute(f"PRAGMA table_info({table})")]


def _target_columns(dst: PgConnection, table: str) -> list[str]:
    return [r[0] for r in dst.execute(
        "SELECT column_name FROM information_schema.columns WHERE table_schema = current_schema() "
        "AND table_name = ? ORDER BY ordinal_position", (table,))]


def migrate(src: sqlite3.Connection, dst: PgConnection, *, dry_run: bool = False, log=print) -> dict[str, int]:
    """Copy every table from ``src`` into ``dst``. Returns rows copied per table."""
    if not is_postgres(dst):
        raise MigrationError("The target must be a PostgreSQL connection.")
    init_schema(dst)  # non-destructive: creates missing tables / columns only

    occupied = [t for t in TABLES if dst.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]]
    if occupied:
        raise MigrationError(
            "Target database already contains data in: " + ", ".join(occupied) + ". Nothing was copied. "
            "Migrate into an empty database (before the app's first start against it, or with "
            "SMARTLAB_SEED_DEMO=false), or clear those tables yourself after taking a backup.")

    source_tables = {r[0] for r in src.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
    copied: dict[str, int] = {}
    try:
        for table in TABLES:
            if table not in source_tables:
                log(f"  {table:<22} not in source, skipped")
                continue
            target_cols = set(_target_columns(dst, table))
            cols = [c for c in _source_columns(src, table) if c in target_cols]
            dropped = [c for c in _source_columns(src, table) if c not in target_cols]
            if dropped:
                raise MigrationError(f"{table}: source columns {dropped} have no target column.")
            rows = [tuple(r) for r in src.execute(f"SELECT {', '.join(cols)} FROM {table} ORDER BY 1")]
            self_ref = SELF_REFERENCES.get(table)
            insert_rows = rows
            if self_ref in cols:
                idx = cols.index(self_ref)
                insert_rows = [r[:idx] + (None,) + r[idx + 1:] for r in rows]
            if insert_rows:
                dst.executemany(
                    f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({', '.join('?' * len(cols))})", insert_rows)
            if self_ref in cols:
                idx = cols.index(self_ref)
                patches = [(r[idx], r[cols.index("id")]) for r in rows if r[idx] is not None]
                if patches:
                    dst.executemany(f"UPDATE {table} SET {self_ref} = ? WHERE id = ?", patches)
            copied[table] = len(rows)
            log(f"  {table:<22} {len(rows):>6} rows")

        for table in TABLES:
            if "id" in _target_columns(dst, table):
                # Continue generated ids after the highest copied id.
                dst.execute(f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), "
                            f"COALESCE(MAX(id), 1), MAX(id) IS NOT NULL) FROM {table}")

        for table, expected in copied.items():
            actual = dst.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            if actual != expected:
                raise MigrationError(f"{table}: expected {expected} rows after copy, found {actual}.")
    except Exception:
        dst.rollback()
        raise

    if dry_run:
        dst.rollback()
        log("Dry run: verified and rolled back. Nothing was written.")
    else:
        dst.commit()
        log("Committed.")
    return copied


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--sqlite", type=Path, default=Config.DATABASE_PATH,
                        help=f"source SQLite file (default: {Config.DATABASE_PATH})")
    parser.add_argument("--dry-run", action="store_true", help="copy and verify, then roll back")
    args = parser.parse_args(argv)

    try:
        engine, url = resolve_database()
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if engine != "postgresql":
        print("error: set SMARTLAB_DATABASE_URL (or DATABASE_URL) to the target PostgreSQL database.",
              file=sys.stderr)
        return 2

    print(f"Source: {args.sqlite} (read-only)")
    print(f"Target: {redact_url(url)}")
    src = _open_sqlite_readonly(args.sqlite)
    dst = connect(url)
    try:
        copied = migrate(src, dst, dry_run=args.dry_run)
    except MigrationError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    finally:
        src.close()
        dst.close()
    print(f"{sum(copied.values())} rows in {len(copied)} tables.")
    if not args.dry_run:
        print("Next: copy the uploads directory to the server (see README, 'Deploying with Supabase').")
    return 0


if __name__ == "__main__":
    sys.exit(main())
