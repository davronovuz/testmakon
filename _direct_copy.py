#!/usr/bin/env python3
"""
Direct SQLite -> PostgreSQL copy.
Django serialize/deserialize ishlatilmaydi.
FK triggers vaqtincha o'chiriladi — tartib muhim emas.
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

# Yuklanmasin (Django schema boshqaradi)
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
        WHERE schemaname = 'public'
        ORDER BY tablename
    """)
    pg_tables = [r[0] for r in cur.fetchall() if r[0] not in SKIP_TABLES]
    print(f"PostgreSQL jadvallar: {len(pg_tables)}", flush=True)

    # SQLite tables
    sq_tables = {
        r[0] for r in sq.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }
    common = [t for t in pg_tables if t in sq_tables]
    print(f"Umumiy jadvallar: {len(common)}", flush=True)

    # 1. FK triggerlarni o'chirish (INSERT tartib muhim emas bo'ladi)
    print("\n[1] FK triggers o'chirilmoqda...", flush=True)
    for t in pg_tables:
        cur.execute(f'ALTER TABLE "{t}" DISABLE TRIGGER ALL')
    print("    OK", flush=True)

    # 2. Mavjud datani tozalash
    print("[2] Eski data o'chirilmoqda...", flush=True)
    for t in reversed(pg_tables):
        cur.execute(f'DELETE FROM "{t}"')
    print("    OK", flush=True)

    # 3. SQLite -> PostgreSQL nusxalash
    print("[3] Ma'lumotlar ko'chirilmoqda...", flush=True)
    total_rows = 0
    errors = []

    for table in sorted(common):
        rows = sq.execute(f'SELECT * FROM "{table}"').fetchall()
        if not rows:
            continue

        cols = list(rows[0].keys())
        col_str = ", ".join(f'"{c}"' for c in cols)

        # Python tuple larga aylantirish
        values = []
        for row in rows:
            values.append(tuple(
                bool(row[c]) if isinstance(row[c], int) and c in ('is_active','is_staff','is_superuser','is_correct','is_published','is_featured','is_read','is_scrolling','is_free') else row[c]
                for c in cols
            ))

        try:
            execute_values(
                cur,
                f'INSERT INTO "{table}" ({col_str}) VALUES %s',
                values,
                page_size=500
            )
            print(f"    ✓ {table}: {len(rows)} qator", flush=True)
            total_rows += len(rows)
        except Exception as e:
            errors.append((table, str(e)[:120]))
            print(f"    ✗ {table}: {str(e)[:80]}", flush=True)
            # Bu jadval uchun transaction ni rollback qilmasdan davom et
            pg.rollback()
            # FK ni qayta o'chir (rollback keyin)
            for t in pg_tables:
                try:
                    cur.execute(f'ALTER TABLE "{t}" DISABLE TRIGGER ALL')
                except:
                    pass

    # 4. FK triggerllarni qayta yoqish
    print("\n[4] FK triggers qayta yoqilmoqda...", flush=True)
    for t in pg_tables:
        cur.execute(f'ALTER TABLE "{t}" ENABLE TRIGGER ALL')
    print("    OK", flush=True)

    # 5. Sequence larni reset qilish
    print("[5] Sequence lar yangilanmoqda...", flush=True)
    cur.execute("""
        SELECT
            seq.relname AS seq_name,
            tab.relname AS tab_name,
            attr.attname AS col_name
        FROM pg_class seq
        JOIN pg_depend dep ON dep.objid = seq.oid
            AND seq.relkind = 'S'
        JOIN pg_class tab ON tab.oid = dep.refobjid
        JOIN pg_attribute attr ON attr.attrelid = tab.oid
            AND attr.attnum = dep.refobjsubid
        JOIN pg_namespace ns ON ns.oid = seq.relnamespace
        WHERE ns.nspname = 'public'
    """)
    seqs = cur.fetchall()
    for seq_name, tab_name, col_name in seqs:
        try:
            cur.execute(f"""
                SELECT setval(
                    '{seq_name}',
                    COALESCE((SELECT MAX("{col_name}") FROM "{tab_name}"), 1),
                    true
                )
            """)
        except Exception as se:
            pass  # Ayrim sequence lar string PK ishlatadi
    print(f"    {len(seqs)} ta sequence yangilandi", flush=True)

    pg.commit()

    print("\n" + "=" * 55, flush=True)
    print(f"  Jami: {total_rows} qator ko'chirildi", flush=True)
    if errors:
        print(f"  Xatolar: {len(errors)} ta jadval", flush=True)
        for t, e in errors:
            print(f"    - {t}: {e}", flush=True)
    else:
        print("  Xatolar: 0", flush=True)
    print("=" * 55, flush=True)
    print("STATUS: OK" if not errors else f"STATUS: PARTIAL ({len(errors)} table failed)")

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
