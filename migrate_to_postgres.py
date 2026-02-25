#!/usr/bin/env python3
"""
TestMakon: SQLite -> PostgreSQL Migration Script
================================================
Ishga tushirish: python3 migrate_to_postgres.py

Nima qiladi:
  1. SQLite dan to'liq backup oladi
  2. Yangi kodni git pull qiladi
  3. PostgreSQL konteyner ishga tushiradi
  4. Ma'lumotlarni PostgreSQL ga ko'chiradi
  5. Natijani tekshiradi
  6. Xato bo'lsa — avtomatik SQLite ga qaytadi (rollback)
"""

import subprocess
import sys
import os
import json
import time
import datetime
from pathlib import Path

# ── Sozlamalar ──────────────────────────────────────────────
WEB_CONTAINER      = "testmakon_web"
POSTGRES_CONTAINER = "testmakon_postgres"
BACKUP_DIR         = Path("./migration_backups")
TIMESTAMP          = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
BACKUP_FILE        = BACKUP_DIR / f"db_backup_{TIMESTAMP}.json"
SQLITE_FILE        = "./db.sqlite3"
SQLITE_BACKUP      = BACKUP_DIR / f"db_sqlite_{TIMESTAMP}.sqlite3"

# docker compose v2 (probel) yoki v1 (tire) avtomatik aniqlanadi
def _detect_compose():
    r = subprocess.run("docker compose version", shell=True, capture_output=True)
    if r.returncode == 0:
        return "docker compose"
    return "docker-compose"

COMPOSE = _detect_compose()

# ── Yordamchi funksiyalar ────────────────────────────────────

def header(msg):
    print(f"\n{'═'*60}")
    print(f"  {msg}")
    print(f"{'═'*60}")

def ok(msg):    print(f"  ✅  {msg}")
def err(msg):   print(f"  ❌  {msg}")
def info(msg):  print(f"  ℹ️   {msg}")
def warn(msg):  print(f"  ⚠️   {msg}")

def run(cmd, check=True, capture=False, silent=False):
    """Shell komanda ishga tushirish"""
    if not silent:
        print(f"     $ {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=capture, text=True)
    if check and result.returncode != 0:
        err(f"Komanda muvaffaqiyatsiz: {cmd}")
        if capture and result.stderr:
            print(f"     STDERR: {result.stderr[:500]}")
        return None
    return result

def run_or_die(cmd, msg=""):
    """Muvaffaqiyatsiz bo'lsa — rollback va chiqish"""
    result = run(cmd, check=False, capture=True, silent=True)
    print(f"     $ {cmd}")
    if result is None or result.returncode != 0:
        err(msg or f"Xato: {cmd}")
        if result and result.stderr:
            print(f"     {result.stderr[:300]}")
        rollback()
        sys.exit(1)
    return result

def container_running(name):
    r = run(f"docker ps --format '{{{{.Names}}}}' | grep -w {name}", check=False, capture=True, silent=True)
    return r is not None and r.returncode == 0 and name in (r.stdout or "")

def get_count(container, model_path):
    """Konteyner ichida model count olish"""
    cmd = f'docker exec {container} python manage.py shell -c "from {model_path.rsplit(".", 1)[0]} import {model_path.rsplit(".", 1)[1]}; print({model_path.rsplit(".", 1)[1]}.objects.count())"'
    r = run(cmd, check=False, capture=True, silent=True)
    if r and r.returncode == 0:
        try:
            return int(r.stdout.strip())
        except:
            return -1
    return -1

# ── Rollback ─────────────────────────────────────────────────

def rollback():
    """Xato bo'lsa SQLite ga qaytish"""
    warn("ROLLBACK boshlandi — SQLite ga qaytilmoqda...")
    run(f"{COMPOSE} down", check=False, capture=True, silent=True)

    # Eski docker-compose ni tiklash
    r = run("git stash", check=False, capture=True, silent=True)

    # SQLite backup ni tiklash
    if SQLITE_BACKUP.exists():
        run(f"cp {SQLITE_BACKUP} {SQLITE_FILE}", check=False)
        ok("SQLite backup tiklandi")

    # Eski konteynerlarni ishga tushirish
    result = run("git stash list", check=False, capture=True, silent=True)
    if result and "stash@{0}" in (result.stdout or ""):
        run("git stash pop", check=False, capture=True, silent=True)

    run(f"{COMPOSE} up -d --build", check=False)
    err("Rollback bajarildi. Sayt eski SQLite bilan ishlayapti.")
    err(f"Backup fayl: {BACKUP_FILE}")

# ── Asosiy funksiyalar ────────────────────────────────────────

def step1_check_prerequisites():
    header("1-QADAM: Tekshiruv")

    # Docker bormi?
    r = run("docker --version", check=False, capture=True, silent=True)
    if not r or r.returncode != 0:
        err("Docker topilmadi!")
        sys.exit(1)
    ok("Docker mavjud")

    # docker compose bormi?
    ok(f"Docker Compose: '{COMPOSE}' topildi")

    # Web konteyner ishlayaptimi?
    if not container_running(WEB_CONTAINER):
        err(f"{WEB_CONTAINER} konteyner ishlamayapti!")
        err(f"Avval saytni ishga tushiring: {COMPOSE} up -d")
        sys.exit(1)
    ok(f"{WEB_CONTAINER} konteyner ishlayapti")

    # SQLite faylmi?
    if not Path(SQLITE_FILE).exists():
        err(f"SQLite fayl topilmadi: {SQLITE_FILE}")
        sys.exit(1)
    size = Path(SQLITE_FILE).stat().st_size / 1024 / 1024
    ok(f"SQLite fayl topildi ({size:.1f} MB)")

    # Backup papka
    BACKUP_DIR.mkdir(exist_ok=True)
    ok(f"Backup papka: {BACKUP_DIR}")


def step2_backup_sqlite():
    header("2-QADAM: SQLite backup")

    # SQLite faylni to'g'ridan-to'g'ri backup
    run(f"cp {SQLITE_FILE} {SQLITE_BACKUP}")
    ok(f"SQLite fayl nusxalandi: {SQLITE_BACKUP}")

    # dumpdata (JSON backup)
    info("dumpdata boshlandi (bir necha daqiqa ketishi mumkin)...")
    r = run(
        f"docker exec {WEB_CONTAINER} python manage.py dumpdata "
        f"--natural-foreign --natural-primary "
        f"--exclude=contenttypes "
        f"--exclude=auth.permission "
        f"--exclude=admin.logentry "
        f"--indent=2 "
        f"-o /app/db_backup_temp.json",
        check=False, capture=True, silent=True
    )
    print(f"     $ dumpdata ...")

    if r is None or r.returncode != 0:
        err("dumpdata muvaffaqiyatsiz!")
        if r: print(f"     {r.stderr[:500]}")
        sys.exit(1)

    # Serverga olib chiqish
    run(f"docker cp {WEB_CONTAINER}:/app/db_backup_temp.json {BACKUP_FILE}")
    run(f"docker exec {WEB_CONTAINER} rm /app/db_backup_temp.json", check=False)

    # Validatsiya
    try:
        with open(BACKUP_FILE) as f:
            data = json.load(f)
        record_count = len(data)
        ok(f"JSON backup saqlandi: {BACKUP_FILE}")
        ok(f"Jami yozuvlar: {record_count:,} ta")
    except Exception as e:
        err(f"Backup fayli buzilgan: {e}")
        sys.exit(1)

    # Joriy user sonini eslab qolish
    user_count = get_count(WEB_CONTAINER, "accounts.models.User")
    info(f"Hozirgi userlar soni: {user_count}")
    return user_count


def step3_git_pull():
    header("3-QADAM: Yangi kodni olish")
    run("git pull")
    ok("git pull bajarildi")


def step4_restart_with_postgres():
    header("4-QADAM: PostgreSQL bilan ishga tushirish")

    info("Konteynerlari to'xtatilmoqda...")
    run(f"{COMPOSE} down")
    ok("Barcha konteynerlar to'xtatildi")

    info("Yangi konteynerlar build qilinmoqda (3-5 daqiqa)...")
    run(f"{COMPOSE} up -d --build")
    ok("Konteynerlar ishga tushirildi")

    # PostgreSQL tayyor bo'lishini kutish
    info("PostgreSQL tayyor bo'lishini kutmoqda...")
    for i in range(30):
        r = run(
            f"docker exec {POSTGRES_CONTAINER} pg_isready -U testmakon_user -d testmakon_db",
            check=False, capture=True, silent=True
        )
        if r and r.returncode == 0:
            ok("PostgreSQL tayyor!")
            break
        time.sleep(3)
        print(f"     ... {(i+1)*3}s", end="\r")
    else:
        err("PostgreSQL 90 sekund ichida tayyor bo'lmadi!")
        rollback()
        sys.exit(1)

    # Web konteyner tayyor bo'lishini kutish
    info("Web konteyner tayyor bo'lishini kutmoqda...")
    time.sleep(5)


def step5_migrate():
    header("5-QADAM: Ma'lumotlar bazasi strukturasi yaratish")

    r = run(
        f"docker exec {WEB_CONTAINER} python manage.py migrate",
        check=False, capture=True, silent=True
    )
    print(f"     $ docker exec {WEB_CONTAINER} python manage.py migrate")

    if r is None or r.returncode != 0:
        err("migrate muvaffaqiyatsiz!")
        if r: print(f"     {r.stderr[:500]}")
        rollback()
        sys.exit(1)

    ok("Barcha migratsiyalar bajarildi")


def step6_load_data():
    header("6-QADAM: Ma'lumotlarni PostgreSQL ga yuklash")

    # Backup faylni konteynerga yuborish
    run(f"docker cp {BACKUP_FILE} {WEB_CONTAINER}:/app/db_backup_load.json")
    ok("Backup fayl konteynerga yuborildi")

    # loaddata
    info("loaddata boshlandi (bir necha daqiqa ketishi mumkin)...")
    r = run(
        f"docker exec {WEB_CONTAINER} python manage.py loaddata /app/db_backup_load.json",
        check=False, capture=True, silent=True
    )
    print(f"     $ docker exec {WEB_CONTAINER} python manage.py loaddata ...")

    if r is None or r.returncode != 0:
        err("loaddata muvaffaqiyatsiz!")
        if r:
            print(f"     STDOUT: {r.stdout[:300]}")
            print(f"     STDERR: {r.stderr[:500]}")
        run(f"docker exec {WEB_CONTAINER} rm -f /app/db_backup_load.json", check=False)
        rollback()
        sys.exit(1)

    # Faylni tozalash
    run(f"docker exec {WEB_CONTAINER} rm /app/db_backup_load.json", check=False)
    ok("Ma'lumotlar yuklandi!")


def step7_verify(expected_users):
    header("7-QADAM: Natijani tekshirish")

    # User soni
    actual_users = get_count(WEB_CONTAINER, "accounts.models.User")
    if actual_users == expected_users:
        ok(f"Userlar: {actual_users} ta ✓ (mos keladi)")
    elif actual_users > 0:
        warn(f"Userlar: {actual_users} ta (kutilgan: {expected_users})")
    else:
        err("Userlar yuklanmagan!")
        rollback()
        sys.exit(1)

    # TestAttempt soni
    r = run(
        f'docker exec {WEB_CONTAINER} python manage.py shell -c '
        f'"from tests_app.models import TestAttempt; print(TestAttempt.objects.count())"',
        check=False, capture=True, silent=True
    )
    if r and r.returncode == 0:
        ok(f"TestAttempt: {r.stdout.strip()} ta ✓")

    # Superuser bormi?
    r = run(
        f'docker exec {WEB_CONTAINER} python manage.py shell -c '
        f'"from accounts.models import User; print(User.objects.filter(is_superuser=True).count())"',
        check=False, capture=True, silent=True
    )
    if r and r.returncode == 0:
        count = r.stdout.strip()
        ok(f"Superuserlar: {count} ta ✓")

    # DB ulanish tekshiruvi
    r = run(
        f'docker exec {WEB_CONTAINER} python manage.py shell -c '
        f'"from django.db import connection; connection.ensure_connection(); print(\'DB OK\')"',
        check=False, capture=True, silent=True
    )
    if r and "DB OK" in (r.stdout or ""):
        ok("PostgreSQL ulanish ishlayapti ✓")


def step8_cleanup():
    header("8-QADAM: Yakunlash")

    # SQLite ni arxivlash (o'chirmaymiz, ehtiyot uchun)
    archived = BACKUP_DIR / f"db_sqlite_{TIMESTAMP}_archived.sqlite3"
    if Path(SQLITE_FILE).exists():
        run(f"mv {SQLITE_FILE} {archived}", check=False)
        ok(f"SQLite fayl arxivlandi: {archived}")
        info("SQLite fayli o'chirilmadi — ehtiyot uchun 30 kun saqlab qo'ying")

    ok(f"JSON backup: {BACKUP_FILE}")
    ok("Migration muvaffaqiyatli yakunlandi!")


# ── Main ─────────────────────────────────────────────────────

def main():
    print()
    print("╔══════════════════════════════════════════════════════╗")
    print("║   TestMakon: SQLite → PostgreSQL Migration           ║")
    print(f"║   Vaqt: {TIMESTAMP}                          ║")
    print("╚══════════════════════════════════════════════════════╝")

    # Tasdiqlash
    print()
    warn("Bu jarayon qaytarib bo'lmaydi (avtomatik rollback mavjud).")
    warn(f"Backup: {BACKUP_FILE}")
    print()
    confirm = input("  Davom etasizmi? (yes deb yozing): ").strip().lower()
    if confirm != "yes":
        info("Bekor qilindi.")
        sys.exit(0)

    try:
        step1_check_prerequisites()
        user_count = step2_backup_sqlite()
        step3_git_pull()
        step4_restart_with_postgres()
        step5_migrate()
        step6_load_data()
        step7_verify(user_count)
        step8_cleanup()

        print()
        print("╔══════════════════════════════════════════════════════╗")
        print("║   ✅  Migration muvaffaqiyatli yakunlandi!           ║")
        print("║   🐘  PostgreSQL ishga tushdi                        ║")
        print("║   🚀  Sayt https://testmakon.uz da ishlayapti        ║")
        print("╚══════════════════════════════════════════════════════╝")
        print()

    except KeyboardInterrupt:
        print()
        warn("Foydalanuvchi to'xtatdi.")
        rollback()
        sys.exit(1)
    except Exception as e:
        err(f"Kutilmagan xato: {e}")
        import traceback
        traceback.print_exc()
        rollback()
        sys.exit(1)


if __name__ == "__main__":
    main()
