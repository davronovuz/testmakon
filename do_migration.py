#!/usr/bin/env python3
"""
TestMakon: SQLite → PostgreSQL migration
Ishlatish: python3 do_migration.py
"""
import subprocess, sys, os, json, time
from pathlib import Path

WEB  = "testmakon_web"
PG   = "testmakon_postgres"
BDIR = Path("./migration_backups")
BDIR.mkdir(exist_ok=True)

def run(cmd, capture=False, silent=False):
    if not silent:
        print(f"    $ {cmd[:120]}")
    r = subprocess.run(cmd, shell=True, capture_output=capture, text=True)
    return r

def ok(m):   print(f"  ✅  {m}")
def err(m):  print(f"  ❌  {m}")
def info(m): print(f"  ℹ️   {m}")
def hdr(m):  print(f"\n{'─'*55}\n  {m}\n{'─'*55}")

# ── 1. Tekshirish ─────────────────────────────────────────
hdr("1. Konteynerlar tekshirilmoqda")

r = run("docker ps --format '{{.Names}}'", capture=True, silent=True)
if WEB not in r.stdout:
    err(f"{WEB} ishlamayapti! docker compose up -d")
    sys.exit(1)
ok(f"{WEB} ishlayapti")
if PG not in r.stdout:
    err(f"{PG} ishlamayapti! docker compose up -d")
    sys.exit(1)
ok(f"{PG} ishlayapti")

sqlite_src = None
for c in ["./db.sqlite3"] + sorted(BDIR.glob("db_sqlite_*.sqlite3"), reverse=True):
    if Path(str(c)).exists() and Path(str(c)).stat().st_size > 10000:
        sqlite_src = str(c)
        break
if not sqlite_src:
    err("SQLite fayl topilmadi!")
    sys.exit(1)
size = Path(sqlite_src).stat().st_size / 1024 / 1024
ok(f"SQLite: {sqlite_src} ({size:.1f} MB)")

# ── 2. Migrate (PostgreSQL schema) ─────────────────────────
hdr("2. PostgreSQL jadvallar yaratilmoqda (migrate)")

r = run(f"docker exec {WEB} python manage.py migrate", capture=True)
if r.returncode != 0:
    err("migrate muvaffaqiyatsiz!")
    print(r.stderr[-400:])
    sys.exit(1)
ok("Barcha migratsiyalar bajarildi")

# ── 3. SQLite konteynerga ko'chirish ───────────────────────
hdr("3. SQLite faylni konteynerga ko'chirish")

r = run(f"docker cp {sqlite_src} {WEB}:/app/_sqlite_tmp.sqlite3")
if r.returncode != 0:
    err("docker cp muvaffaqiyatsiz!")
    sys.exit(1)
ok("SQLite konteynerga ko'chirildi")

# ── 4. Direct copy skriptini ko'chirish va ishlatish ────────
hdr("4. Ma'lumotlar PostgreSQL ga ko'chirilmoqda")

# _direct_copy.py ni git repo dan olish (alohida fayl)
copy_script = Path("_direct_copy.py")
if not copy_script.exists():
    err("_direct_copy.py topilmadi!")
    sys.exit(1)

run(f"docker cp _direct_copy.py {WEB}:/app/_direct_copy.py")
info("Direct copy ishlamoqda (1-3 daqiqa)...")

r = run(f"docker exec {WEB} python /app/_direct_copy.py", capture=True)
output = r.stdout.strip()
print("\n" + "\n".join("    " + l for l in output.splitlines()))

if r.returncode != 0 or "STATUS: OK" not in r.stdout:
    err("Copy muvaffaqiyatsiz!")
    if r.stderr:
        print(r.stderr[-400:])
    sys.exit(1)
ok("Ma'lumotlar yuklandi!")

# ── 5. Tekshirish ──────────────────────────────────────────
hdr("5. Tekshirish")

checks = [
    ("accounts.models.User",            "Userlar"),
    ("tests_app.models.Question",        "Savollar"),
    ("tests_app.models.TestAttempt",     "TestAttempt"),
]
for model_path, label in checks:
    app, mdl = model_path.rsplit(".", 1)
    r = run(
        f'docker exec {WEB} python manage.py shell -c '
        f'"from {app} import {mdl}; print({mdl}.objects.count())"',
        capture=True, silent=True
    )
    count = r.stdout.strip() if r.returncode == 0 else "xato"
    icon = "✅" if count not in ("0", "xato") else "⚠️"
    print(f"  {icon}  {label}: {count} ta")

# Tozalash
run(f"docker exec {WEB} rm -f /app/_direct_copy.py /app/_sqlite_tmp.sqlite3",
    capture=True, silent=True)

print()
print("╔══════════════════════════════════════════════════════╗")
print("║  ✅  Migration muvaffaqiyatli yakunlandi!            ║")
print("║  🐘  Sayt endi PostgreSQL bilan ishlayapti           ║")
print("╚══════════════════════════════════════════════════════╝")
