#!/usr/bin/env python3
"""
Direct SQLite -> PostgreSQL copy.
- Boolean kolumnlar PostgreSQL schema dan avtomatik aniqlanadi
- Har jadval uchun SAVEPOINT — bitta xato hamma narsani bekor qilmaydi
- FK triggers o'chiriladi — tartib muhim emas
"""
import sqlite3, os, sys
import psycopg2
from psycopg2.extras import execute_values

print("=" * 55, flush=True)
print("  Direct SQLite -> PostgreSQL copy", flush=True)
print("=" * 55, flush=True)

SQ_FILE = "/app/_sqlite_tmp.sqlite3"
DB_URL  = os.environ.get(
    "DATABASE_URL",
    "postgres://testmakon_user:TestMakon2024!@postgres:5432/testmakon_db"
)

SKIP_TABLES = {
    "django_migrations",
    "django_content_type",
    "auth_permission",
    "django_admin_log",
}

sq = sqlite3.connect(SQ_FILE)
sq.row_factory = sqlite3.Row

pg = psycopg2.connect(DB_URL)
pg.autocommit = False
cur = pg.cursor()

try:
    # PostgreSQL tables
    cur.execute("""
        SELECT tablename FROM pg_tables
        WHERE schemaname = 'public' ORDER BY tablename
    """)
    pg_tables = [r[0] for r in cur.fetchall() if r[0] not in SKIP_TABLES]

    # SQLite tables
    sq_tables = {
        r[0] for r in sq.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }
    common = [t for t in pg_tables if t in sq_tables]
    print(f"PostgreSQL: {len(pg_tables)} | Umumiy: {len(common)}", flush=True)

    # Boolean kolumnlarni PostgreSQL schema dan olish (hardcoded emas!)
    cur.execute("""
        SELECT table_name, column_name
        FROM information_schema.columns
        WHERE table_schema = 'public' AND data_type = 'boolean'
    """)
    bool_cols = {(r[0], r[1]) for r in cur.fetchall()}
    print(f"Boolean kolumnlar: {len(bool_cols)} ta", flush=True)

    # ── 1. FK triggers o'chirish ───────────────────────────────
    print("\n[1] FK triggers o'chirilmoqda...", flush=True)
    for t in pg_tables:
        cur.execute(f'ALTER TABLE "{t}" DISABLE TRIGGER ALL')
    print("    OK", flush=True)

    # ── 2. Eski datani tozalash ────────────────────────────────
    # (Savepoint ishlatiladi — DELETE outer transaksiyada qoladi)
    print("[2] Eski data o'chirilmoqda...", flush=True)
    for t in reversed(pg_tables):
        cur.execute(f'DELETE FROM "{t}"')
    print("    OK", flush=True)

    # ── 3. SQLite → PostgreSQL nusxalash ───────────────────────
    print("[3] Ma'lumotlar ko'chirilmoqda...", flush=True)
    total = 0
    errors = []

    for table in sorted(common):
        rows = sq.execute(f'SELECT * FROM "{table}"').fetchall()
        if not rows:
            continue

        cols = list(rows[0].keys())
        col_str = ", ".join(f'"{c}"' for c in cols)

        # Boolean conversion: SQLite 0/1 → Python True/False
        values = []
        for row in rows:
            vals = []
            for c in cols:
                v = row[c]
                if v is not None and (table, c) in bool_cols:
                    v = bool(int(v))
                vals.append(v)
            values.append(tuple(vals))

        # SAVEPOINT — xato bo'lsa faqat shu jadval rollback, DELETE saqlanadi
        cur.execute("SAVEPOINT sp_table")
        try:
            execute_values(
                cur,
                f'INSERT INTO "{table}" ({col_str}) VALUES %s',
                values,
                page_size=500
            )
            cur.execute("RELEASE SAVEPOINT sp_table")
            print(f"    ✓ {table}: {len(rows)} qator", flush=True)
            total += len(rows)
        except Exception as e:
            cur.execute("ROLLBACK TO SAVEPOINT sp_table")
            cur.execute("RELEASE SAVEPOINT sp_table")
            errors.append((table, str(e)[:100]))
            print(f"    ✗ {table}: {str(e)[:80]}", flush=True)

    # ── 4. FK triggers qayta yoqish ────────────────────────────
    print("\n[4] FK triggers qayta yoqilmoqda...", flush=True)
    for t in pg_tables:
        cur.execute(f'ALTER TABLE "{t}" ENABLE TRIGGER ALL')
    print("    OK", flush=True)

    # ── 5. Sequence lar reset ──────────────────────────────────
    print("[5] Sequence lar yangilanmoqda...", flush=True)
    cur.execute("""
        SELECT seq.relname, tab.relname, attr.attname
        FROM pg_class seq
        JOIN pg_depend dep ON dep.objid = seq.oid AND seq.relkind = 'S'
        JOIN pg_class tab ON tab.oid = dep.refobjid
        JOIN pg_attribute attr ON attr.attrelid = tab.oid
            AND attr.attnum = dep.refobjsubid
        JOIN pg_namespace ns ON ns.oid = seq.relnamespace
        WHERE ns.nspname = 'public'
    """)
    seqs = cur.fetchall()
    reset_ok = 0
    for seq_name, tab_name, col_name in seqs:
        try:
            cur.execute(f"""
                SELECT setval(
                    '{seq_name}',
                    COALESCE((SELECT MAX("{col_name}") FROM "{tab_name}"), 1),
                    true
                )
            """)
            reset_ok += 1
        except:
            pass
    print(f"    {reset_ok}/{len(seqs)} ta sequence yangilandi", flush=True)

    pg.commit()

    # ── Natija ────────────────────────────────────────────────
    print(f"\n{'='*55}", flush=True)
    print(f"  Jami: {total} qator ko'chirildi", flush=True)
    if errors:
        print(f"  Xatolar: {len(errors)} ta jadval", flush=True)
        for t, e in errors:
            print(f"    ✗ {t}: {e}", flush=True)
    else:
        print("  Xatolar: 0 ✓", flush=True)
    print("=" * 55, flush=True)

    if not errors:
        print("STATUS: OK")
    else:
        # Kritik jadvallar tekshiruvi
        critical = {'accounts_user', 'tests_app_question', 'tests_app_test',
                    'tests_app_topic', 'tests_app_subject'}
        failed_critical = critical & {t for t, _ in errors}
        if failed_critical:
            print(f"STATUS: ERRORS (kritik jadvallar: {failed_critical})")
            sys.exit(1)
        else:
            print(f"STATUS: OK (minor: {len(errors)} non-critical table failed)")

except Exception as e:
    pg.rollback()
    print(f"\nKRITIK XATO: {e}", flush=True)
    import traceback
    traceback.print_exc()
    print("STATUS: ERRORS")
    sys.exit(1)
finally:
    pg.close()
    sq.close()
