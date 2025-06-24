#!/usr/bin/env python3
"""
POS Tizimi - Django migratsiyalarini yaratish va qo'llash
"""

import os
import sys
import subprocess
import django
from pathlib import Path

# Django loyihasi yo'lini qo'shish
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Django sozlamalarini yuklash
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pos_system.settings')


def run_command(command, description):
    """Buyruqni ishga tushirish va natijani ko'rsatish"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
        if result.stdout:
            print(f"   ✅ {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Xatolik: {e.stderr.strip()}")
        return False


def check_django_setup():
    """Django sozlamalarini tekshirish"""
    print("🔍 Django sozlamalarini tekshirish...")
    try:
        django.setup()
        from django.conf import settings
        print(f"   ✅ Django sozlamalari yuklandi")
        print(f"   📁 Loyiha: {settings.BASE_DIR}")
        print(f"   🗄️ Ma'lumotlar bazasi: {settings.DATABASES['default']['ENGINE']}")
        return True
    except Exception as e:
        print(f"   ❌ Django sozlamalarida xatolik: {e}")
        return False


def check_models():
    """Modellarni tekshirish"""
    print("📋 Modellarni tekshirish...")
    try:
        from pos_app.models import Category, Product, ProductBatch, Sale, SaleItem, ReturnSale, ReturnItem

        models = [
            ('Category', Category),
            ('Product', Product),
            ('ProductBatch', ProductBatch),
            ('Sale', Sale),
            ('SaleItem', SaleItem),
            ('ReturnSale', ReturnSale),
            ('ReturnItem', ReturnItem)
        ]

        for model_name, model_class in models:
            fields = [f.name for f in model_class._meta.fields]
            print(f"   ✅ {model_name}: {len(fields)} ta maydon")

        return True
    except Exception as e:
        print(f"   ❌ Modellarda xatolik: {e}")
        return False


def create_initial_migration():
    """Boshlang'ich migratsiya yaratish"""
    print("📝 Boshlang'ich migratsiya yaratish...")

    # Eski migratsiyalarni o'chirish (agar kerak bo'lsa)
    migrations_dir = Path('pos_app/migrations')
    if migrations_dir.exists():
        migration_files = list(migrations_dir.glob('*.py'))
        migration_files = [f for f in migration_files if f.name != '__init__.py']

        if migration_files:
            print(f"   📁 {len(migration_files)} ta eski migratsiya topildi")
            response = input("   ❓ Eski migratsiyalarni o'chirishni xohlaysizmi? (y/N): ")
            if response.lower() == 'y':
                for migration_file in migration_files:
                    migration_file.unlink()
                    print(f"   🗑️ {migration_file.name} o'chirildi")

    # Yangi migratsiya yaratish
    return run_command(
        "python manage.py makemigrations pos_app --name initial_pos_models",
        "Yangi migratsiya yaratish"
    )


def apply_migrations():
    """Migratsiyalarni qo'llash"""
    print("⚡ Migratsiyalarni qo'llash...")

    # Django asosiy migratsiyalari
    if not run_command("python manage.py migrate auth", "Auth migratsiyalari"):
        return False

    if not run_command("python manage.py migrate contenttypes", "ContentTypes migratsiyalari"):
        return False

    if not run_command("python manage.py migrate sessions", "Sessions migratsiyalari"):
        return False

    if not run_command("python manage.py migrate admin", "Admin migratsiyalari"):
        return False

    # POS app migratsiyalari
    if not run_command("python manage.py migrate pos_app", "POS app migratsiyalari"):
        return False

    return True


def check_migration_status():
    """Migratsiya holatini tekshirish"""
    print("📊 Migratsiya holatini tekshirish...")
    return run_command("python manage.py showmigrations", "Migratsiya holati")


def create_database_schema():
    """Ma'lumotlar bazasi sxemasini yaratish"""
    print("🏗️ Ma'lumotlar bazasi sxemasini yaratish...")

    # SQLite uchun ma'lumotlar bazasi faylini yaratish
    db_file = Path('db.sqlite3')
    if not db_file.exists():
        print("   📁 SQLite ma'lumotlar bazasi yaratilmoqda...")
        db_file.touch()

    return True


def validate_models():
    """Modellarni validatsiya qilish"""
    print("✅ Modellarni validatsiya qilish...")
    return run_command("python manage.py check", "Model validatsiyasi")


def main():
    """Asosiy funksiya"""
    print("🚀 POS Tizimi migratsiyalarini yaratish va qo'llash\n")

    steps = [
        ("Django sozlamalarini tekshirish", check_django_setup),
        ("Modellarni tekshirish", check_models),
        ("Ma'lumotlar bazasi sxemasini yaratish", create_database_schema),
        ("Boshlang'ich migratsiya yaratish", create_initial_migration),
        ("Migratsiyalarni qo'llash", apply_migrations),
        ("Modellarni validatsiya qilish", validate_models),
        ("Migratsiya holatini tekshirish", check_migration_status),
    ]

    failed_steps = []

    for step_name, step_function in steps:
        print(f"\n{'=' * 50}")
        if not step_function():
            failed_steps.append(step_name)
            print(f"❌ {step_name} muvaffaqiyatsiz!")
        else:
            print(f"✅ {step_name} muvaffaqiyatli!")

    print(f"\n{'=' * 50}")

    if failed_steps:
        print("❌ Ba'zi qadamlar muvaffaqiyatsiz bo'ldi:")
        for step in failed_steps:
            print(f"   - {step}")
        print("\n🔧 Xatoliklarni tuzatib, qaytadan urinib ko'ring.")
        sys.exit(1)
    else:
        print("✅ Barcha migratsiyalar muvaffaqiyatli yaratildi va qo'llandi!")
        print("\n📋 Keyingi qadamlar:")
        print("   1. python scripts/setup_database.py - Ma'lumotlar bazasini to'ldirish")
        print("   2. python manage.py runserver - Serverni ishga tushirish")
        print("   3. http://127.0.0.1:8000/ - Tizimni ochish")

        print("\n🎯 Foydali buyruqlar:")
        print("   python manage.py createsuperuser - Yangi admin yaratish")
        print("   python manage.py shell - Django shell")
        print("   python manage.py dbshell - Ma'lumotlar bazasi shell")


if __name__ == '__main__':
    main()
