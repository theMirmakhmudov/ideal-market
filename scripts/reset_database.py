#!/usr/bin/env python3
"""
POS Tizimi - Ma'lumotlar bazasini qayta tiklash
"""

import os
import sys
import subprocess
from pathlib import Path


def run_command(command, description):
    """Buyruqni ishga tushirish"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
        if result.stdout:
            print(f"   ✅ {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Xatolik: {e.stderr.strip()}")
        return False


def reset_database():
    """Ma'lumotlar bazasini qayta tiklash"""
    print("🗑️ Ma'lumotlar bazasini qayta tiklash...\n")

    # 1. SQLite faylini o'chirish
    db_file = Path('db.sqlite3')
    if db_file.exists():
        db_file.unlink()
        print("   ✅ SQLite ma'lumotlar bazasi o'chirildi")

    # 2. Migratsiya fayllarini o'chirish
    migrations_dir = Path('pos_app/migrations')
    if migrations_dir.exists():
        migration_files = list(migrations_dir.glob('*.py'))
        migration_files = [f for f in migration_files if f.name != '__init__.py']

        for migration_file in migration_files:
            migration_file.unlink()
            print(f"   🗑️ {migration_file.name} o'chirildi")

    # 3. __pycache__ papkalarini tozalash
    for pycache_dir in Path('.').rglob('__pycache__'):
        if pycache_dir.is_dir():
            import shutil
            shutil.rmtree(pycache_dir)
            print(f"   🧹 {pycache_dir} tozalandi")

    print("\n✅ Ma'lumotlar bazasi muvaffaqiyatli qayta tiklandi!")
    print("\n📋 Keyingi qadamlar:")
    print("   1. python scripts/create_migrations.py")
    print("   2. python scripts/setup_database.py")


def main():
    """Asosiy funksiya"""
    print("⚠️  DIQQAT: Bu amal barcha ma'lumotlarni o'chiradi!")
    response = input("Davom etishni xohlaysizmi? (y/N): ")

    if response.lower() != 'y':
        print("❌ Amal bekor qilindi.")
        sys.exit(0)

    reset_database()


if __name__ == '__main__':
    main()
