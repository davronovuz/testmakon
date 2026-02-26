#!/usr/bin/env python3
"""
TestMakon: SQLite → PostgreSQL ma'lumotlar ko'chirish
Ishlatish: python3 do_migration.py
"""
import subprocess, sys, os, json, time
from pathlib import Path

WEB  = "testmakon_web"
PG   = "testmakon_postgres"
BDIR = Path("./migration_backups")
BDIR.mkdir(exist_ok=True)
BACKUP_JSON = BDIR / "final_backup.json"

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
running = r.stdout
if WEB not in running:
    err(f"{WEB} ishlamayapti! Avval: docker compose up -d")
    sys.exit(1)
ok(f"{WEB} ishlayapti")

if PG not in running:
    err(f"{PG} ishlamayapti! Avval: docker compose up -d")
    sys.exit(1)
ok(f"{PG} ishlayapti")

# SQLite faylni toping
sqlite_src = None
for candidate in ["./db.sqlite3"] + sorted(BDIR.glob("db_sqlite_*.sqlite3"), reverse=True):
    if Path(candidate).exists() and Path(candidate).stat().st_size > 1000:
        sqlite_src = str(candidate)
        break

if not sqlite_src:
    err("SQLite fayl topilmadi!")
    sys.exit(1)
size = Path(sqlite_src).stat().st_size / 1024 / 1024
ok(f"SQLite: {sqlite_src} ({size:.1f} MB)")

# ── 2. PostgreSQL migrate ──────────────────────────────────
hdr("2. PostgreSQL jadvallar yaratilmoqda (migrate)")

r = run(f"docker exec {WEB} python manage.py migrate", capture=True)
if r.returncode != 0:
    err("migrate muvaffaqiyatsiz!")
    print(r.stderr[-600:])
    sys.exit(1)
ok("Barcha migratsiyalar bajarildi")

# ── 3. SQLite → JSON dump ──────────────────────────────────
hdr("3. SQLite dan ma'lumotlar olinmoqda")

# SQLite faylni konteynerga ko'chirish
run(f"docker cp {sqlite_src} {WEB}:/app/_sqlite_tmp.sqlite3")
ok("SQLite konteynerga ko'chirildi")

# Dump scriptini HOST da yozamiz — paste muammosi yo'q
DUMP_PY = '''\
import os, sys
os.environ["DATABASE_URL"] = "sqlite:////app/_sqlite_tmp.sqlite3"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
django.setup()
from django.core.management import call_command
out = open("/tmp/_backup.json", "w")
call_command(
    "dumpdata",
    "--natural-foreign", "--natural-primary",
    "--exclude=contenttypes",
    "--exclude=auth.permission",
    "--exclude=admin.logentry",
    "--indent=2",
    stdout=out,
)
out.close()
size = os.path.getsize("/tmp/_backup.json")
print(f"OK {size}")
'''

with open("/tmp/_dump.py", "w") as f:
    f.write(DUMP_PY)

run(f"docker cp /tmp/_dump.py {WEB}:/app/_dump.py")
info("Dumpdata ishlamoqda (bir necha daqiqa)...")
r = run(f"docker exec {WEB} python /app/_dump.py", capture=True)
print("   ", r.stdout.strip())
if r.returncode != 0 or "OK" not in r.stdout:
    err("Dumpdata muvaffaqiyatsiz!")
    print(r.stderr[-600:])
    sys.exit(1)

# Backup JSON ni serverga olib chiqish
run(f"docker cp {WEB}:/tmp/_backup.json {BACKUP_JSON}")

try:
    with open(BACKUP_JSON) as f:
        data = json.load(f)
    ok(f"JSON backup tayyor: {len(data):,} yozuv")
    users = sum(1 for x in data if x.get("model") in ("accounts.user","auth.user"))
    info(f"Userlar: {users} ta")
except Exception as e:
    err(f"JSON xato: {e}")
    sys.exit(1)

# ── 4. PostgreSQL ga yuklash ───────────────────────────────
hdr("4. Ma'lumotlar PostgreSQL ga yuklanmoqda")

run(f"docker cp {BACKUP_JSON} {WEB}:/app/_backup_load.json")

# Custom load script:
# 1. Signallarni o'chiradi (duplicate key muammosini oldini oladi)
# 2. JSON ni to'g'ri tartibda yuklaydi (User birinchi — natural key uchun)
# 3. Iteratsiya paytida DeserializationError larni ushlaydi
LOAD_PY = '''\
import os, json
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
django.setup()

# 1. Barcha signallarni o\'chirish (post_save signallari duplicate yaratarkan)
from django.db.models.signals import post_save, pre_save, post_delete, pre_delete
for sig in [post_save, pre_save, post_delete, pre_delete]:
    sig.receivers = []
print("Signals disabled", flush=True)

# 2. JSON o\'qish va muhim modellarni birinchi qo\'yish
with open("/app/_backup_load.json") as f:
    data = json.load(f)
print(f"Total: {len(data)} objects", flush=True)

FIRST = [
    "accounts.user", "accounts.userprofile",
    "tests_app.subject", "tests_app.topic",
    "tests_app.test", "tests_app.question", "tests_app.testquestion",
]
data.sort(key=lambda x: (0 if x.get("model","") in FIRST else 1, x.get("model","")))

# 3. Bitta-bitta deserialize va save (tartib muhim — User avval saqlanadi,
#    keyin Friendship uni natural key orqali topadi)
from django.core import serializers as dj_ser
raw = json.dumps(data)

saved = dup_skip = deser_skip = err = 0
gen = dj_ser.deserialize(
    "json", raw,
    use_natural_foreign_keys=True,
    use_natural_primary_keys=True,
    ignorenonexistent=True,
)
while True:
    try:
        obj = next(gen)
    except StopIteration:
        break
    except Exception as de:
        deser_skip += 1
        if deser_skip <= 5:
            print(f"  DeserSkip: {str(de)[:120]}")
        continue
    try:
        obj.save()
        saved += 1
    except Exception as e:
        msg = str(e).lower()
        if "duplicate" in msg or "unique" in msg or "already exists" in msg:
            dup_skip += 1
        else:
            err += 1
            if err <= 5:
                print(f"  ERR {obj.object.__class__.__name__}: {str(e)[:100]}")

print(f"Saved={saved} DupSkip={dup_skip} DeserSkip={deser_skip} Errors={err}")
if err == 0:
    print("STATUS: OK")
else:
    print("STATUS: ERRORS")
'''

with open("/tmp/_load.py", "w") as f:
    f.write(LOAD_PY)
run(f"docker cp /tmp/_load.py {WEB}:/app/_load.py")

info("Loaddata ishlamoqda (bir necha daqiqa)...")
r = run(f"docker exec {WEB} python /app/_load.py", capture=True)
print("  ", r.stdout.strip().replace("\n", "\n   "))
if r.returncode != 0 or "STATUS: OK" not in r.stdout:
    err("Loaddata muvaffaqiyatsiz!")
    print(r.stderr[-400:])
    sys.exit(1)
ok("Ma'lumotlar yuklandi!")

# ── 5. Tekshirish ──────────────────────────────────────────
hdr("5. Tekshirish")

checks = [
    ("accounts.models.User", "Userlar"),
    ("tests_app.models.Question", "Savollar"),
    ("tests_app.models.TestAttempt", "TestAttempt"),
]
all_ok = True
for model_path, label in checks:
    app, model = model_path.rsplit(".", 1)
    r = run(
        f'docker exec {WEB} python manage.py shell -c '
        f'"from {app} import {model}; print({model}.objects.count())"',
        capture=True, silent=True
    )
    count = r.stdout.strip() if r.returncode == 0 else "xato"
    if count == "0" or count == "xato":
        all_ok = False
    print(f"  {'✅' if count not in ('0','xato') else '⚠️'}  {label}: {count} ta")

# Temp fayllarni tozalash
run(f"docker exec {WEB} rm -f /app/_dump.py /app/_sqlite_tmp.sqlite3 /app/_backup_load.json", capture=True, silent=True)

print()
if all_ok:
    print("╔══════════════════════════════════════════════════════╗")
    print("║  ✅  Migration muvaffaqiyatli yakunlandi!            ║")
    print("║  🐘  Sayt endi PostgreSQL bilan ishlayapti           ║")
    print("╚══════════════════════════════════════════════════════╝")
else:
    print("╔══════════════════════════════════════════════════════╗")
    print("║  ⚠️   Tekshirib ko'ring — ba'zi ma'lumotlar 0        ║")
    print(f"║  Backup saqlangan: {BACKUP_JSON}   ║")
    print("╚══════════════════════════════════════════════════════╝")
