#!/usr/bin/env python3
"""
POS Tizimi - Ma'lumotlar bazasini zaxiralash
"""

import os
import sys
import django
import json
from datetime import datetime
from pathlib import Path

# Django loyihasi yo'lini qo'shish
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Django sozlamalarini yuklash
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pos_system.settings')
django.setup()

from django.core import serializers
from pos_app.models import Category, Product, ProductBatch, Sale, SaleItem, ReturnSale, ReturnItem


def create_backup():
    """Ma'lumotlar bazasini zaxiralash"""
    print("💾 Ma'lumotlar bazasini zaxiralash...\n")

    # Zaxira papkasini yaratish
    backup_dir = Path('backups')
    backup_dir.mkdir(exist_ok=True)

    # Zaxira fayl nomi
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = backup_dir / f'pos_backup_{timestamp}.json'

    # Barcha modellarni eksport qilish
    models_to_backup = [
        Category, Product, ProductBatch, Sale, SaleItem, ReturnSale, ReturnItem
    ]

    all_data = []

    for model in models_to_backup:
        model_name = model.__name__
        objects = model.objects.all()
        count = objects.count()

        if count > 0:
            serialized_data = serializers.serialize('json', objects)
            model_data = json.loads(serialized_data)

            all_data.extend(model_data)
            print(f"   ✅ {model_name}: {count} ta yozuv")
        else:
            print(f"   ⚪ {model_name}: bo'sh")

    # Faylga yozish
    with open(backup_file, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)

    file_size = backup_file.stat().st_size / 1024  # KB

    print(f"\n✅ Zaxira muvaffaqiyatli yaratildi!")
    print(f"   📁 Fayl: {backup_file}")
    print(f"   📊 Hajmi: {file_size:.1f} KB")
    print(f"   📋 Jami yozuvlar: {len(all_data)}")


def list_backups():
    """Mavjud zaxiralarni ko'rsatish"""
    print("📋 Mavjud zaxiralar:\n")

    backup_dir = Path('backups')
    if not backup_dir.exists():
        print("   ⚪ Hech qanday zaxira topilmadi")
        return

    backup_files = list(backup_dir.glob('pos_backup_*.json'))

    if not backup_files:
        print("   ⚪ Hech qanday zaxira topilmadi")
        return

    backup_files.sort(reverse=True)  # Eng yangi birinchi

    for i, backup_file in enumerate(backup_files, 1):
        file_size = backup_file.stat().st_size / 1024  # KB
        modified_time = datetime.fromtimestamp(backup_file.stat().st_mtime)

        print(f"   {i}. {backup_file.name}")
        print(f"      📅 Sana: {modified_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"      📊 Hajmi: {file_size:.1f} KB")
        print()


def main():
    """Asosiy funksiya"""
    if len(sys.argv) > 1 and sys.argv[1] == 'list':
        list_backups()
    else:
        create_backup()


if __name__ == '__main__':
    main()
