#!/usr/bin/env python3
"""
POS Tizimi - Ma'lumotlar bazasini sozlash va boshlang'ich ma'lumotlar
"""

import os
import sys
import django
from datetime import datetime, timedelta
from decimal import Decimal

# Django loyihasi yo'lini qo'shish
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Django sozlamalarini yuklash
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pos_system.settings')
django.setup()

from django.contrib.auth.models import User
from pos_app.models import Category, Product, ProductBatch, Sale, SaleItem


def create_superuser():
    """Superuser yaratish"""
    print("🔐 Superuser yaratish...")

    if User.objects.filter(username='admin').exists():
        print("   ✅ Admin foydalanuvchi allaqachon mavjud")
        return User.objects.get(username='admin')

    admin_user = User.objects.create_superuser(
        username='admin',
        email='admin@pos.uz',
        password='admin123',
        first_name='Admin',
        last_name='User'
    )
    print("   ✅ Admin foydalanuvchi yaratildi (admin/admin123)")
    return admin_user


def create_staff_users():
    """Xodimlar yaratish"""
    print("👥 Xodimlar yaratish...")

    staff_users = [
        {
            'username': 'kassir1',
            'password': 'kassir123',
            'first_name': 'Aziza',
            'last_name': 'Karimova',
            'email': 'aziza@pos.uz'
        },
        {
            'username': 'kassir2',
            'password': 'kassir123',
            'first_name': 'Bobur',
            'last_name': 'Toshmatov',
            'email': 'bobur@pos.uz'
        },
        {
            'username': 'manager1',
            'password': 'manager123',
            'first_name': 'Dilshod',
            'last_name': 'Rahimov',
            'email': 'dilshod@pos.uz'
        }
    ]

    created_users = []
    for user_data in staff_users:
        if User.objects.filter(username=user_data['username']).exists():
            print(f"   ✅ {user_data['username']} allaqachon mavjud")
            created_users.append(User.objects.get(username=user_data['username']))
            continue

        user = User.objects.create_user(
            username=user_data['username'],
            password=user_data['password'],
            first_name=user_data['first_name'],
            last_name=user_data['last_name'],
            email=user_data['email']
        )

        # Manager uchun staff huquqi berish
        if 'manager' in user_data['username']:
            user.is_staff = True
            user.save()

        created_users.append(user)
        print(f"   ✅ {user_data['username']} yaratildi")

    return created_users


def create_categories():
    """Kategoriyalar yaratish"""
    print("📂 Kategoriyalar yaratish...")

    categories_data = [
        'Oziq-ovqat',
        'Ichimliklar',
        'Uy-ro\'zg\'or buyumlari',
        'Maktab buyumlari',
        'Kiyim-kechak',
        'Elektronika',
        'Salomatlik',
        'Go\'zallik',
        'Sport',
        'Kitoblar'
    ]

    created_categories = []
    for category_name in categories_data:
        category, created = Category.objects.get_or_create(name=category_name)
        if created:
            print(f"   ✅ {category_name} kategoriyasi yaratildi")
        else:
            print(f"   ✅ {category_name} allaqachon mavjud")
        created_categories.append(category)

    return created_categories


def create_products_and_batches(categories, admin_user):
    """Mahsulotlar va partiyalar yaratish"""
    print("📦 Mahsulotlar va partiyalar yaratish...")

    products_data = [
        # Oziq-ovqat
        {
            'barcode': '1001', 'name': 'Non (Oq)', 'category': 'Oziq-ovqat', 'unit': 'piece',
            'batches': [
                {'purchase_price': 1500, 'selling_price': 2000, 'quantity': 100, 'days_to_expire': 2},
                {'purchase_price': 1600, 'selling_price': 2200, 'quantity': 50, 'days_to_expire': 1}
            ]
        },
        {
            'barcode': '1002', 'name': 'Sut (1L)', 'category': 'Oziq-ovqat', 'unit': 'piece',
            'batches': [
                {'purchase_price': 6000, 'selling_price': 8000, 'quantity': 40, 'days_to_expire': 5},
                {'purchase_price': 6200, 'selling_price': 8500, 'quantity': 30, 'days_to_expire': 7}
            ]
        },
        {
            'barcode': '1003', 'name': 'Tuxum (10 dona)', 'category': 'Oziq-ovqat', 'unit': 'piece',
            'batches': [
                {'purchase_price': 12000, 'selling_price': 15000, 'quantity': 25, 'days_to_expire': 14}
            ]
        },
        {
            'barcode': '1004', 'name': 'Guruch (1kg)', 'category': 'Oziq-ovqat', 'unit': 'kg',
            'batches': [
                {'purchase_price': 9000, 'selling_price': 12000, 'quantity': 50, 'days_to_expire': 365},
                {'purchase_price': 9500, 'selling_price': 13000, 'quantity': 30, 'days_to_expire': 400}
            ]
        },
        {
            'barcode': '1005', 'name': 'Makaron', 'category': 'Oziq-ovqat', 'unit': 'piece',
            'batches': [
                {'purchase_price': 5000, 'selling_price': 7000, 'quantity': 60, 'days_to_expire': 180}
            ]
        },
        {
            'barcode': '1006', 'name': 'Choy (Qora)', 'category': 'Oziq-ovqat', 'unit': 'piece',
            'batches': [
                {'purchase_price': 18000, 'selling_price': 25000, 'quantity': 20, 'days_to_expire': 730}
            ]
        },
        {
            'barcode': '1007', 'name': 'Qahva', 'category': 'Oziq-ovqat', 'unit': 'piece',
            'batches': [
                {'purchase_price': 25000, 'selling_price': 35000, 'quantity': 15, 'days_to_expire': 365}
            ]
        },
        {
            'barcode': '1008', 'name': 'Shakar (1kg)', 'category': 'Oziq-ovqat', 'unit': 'kg',
            'batches': [
                {'purchase_price': 8000, 'selling_price': 11000, 'quantity': 40, 'days_to_expire': 365}
            ]
        },
        {
            'barcode': '1009', 'name': 'Tuz (1kg)', 'category': 'Oziq-ovqat', 'unit': 'kg',
            'batches': [
                {'purchase_price': 2000, 'selling_price': 3000, 'quantity': 50, 'days_to_expire': 1000}
            ]
        },
        {
            'barcode': '1010', 'name': 'Yog\' (1L)', 'category': 'Oziq-ovqat', 'unit': 'liter',
            'batches': [
                {'purchase_price': 15000, 'selling_price': 20000, 'quantity': 25, 'days_to_expire': 365}
            ]
        },

        # Ichimliklar
        {
            'barcode': '2001', 'name': 'Coca Cola (0.5L)', 'category': 'Ichimliklar', 'unit': 'piece',
            'batches': [
                {'purchase_price': 4500, 'selling_price': 6000, 'quantity': 80, 'days_to_expire': 120},
                {'purchase_price': 4700, 'selling_price': 6500, 'quantity': 40, 'days_to_expire': 150}
            ]
        },
        {
            'barcode': '2002', 'name': 'Pepsi (0.5L)', 'category': 'Ichimliklar', 'unit': 'piece',
            'batches': [
                {'purchase_price': 4200, 'selling_price': 5500, 'quantity': 60, 'days_to_expire': 110}
            ]
        },
        {
            'barcode': '2003', 'name': 'Suv (0.5L)', 'category': 'Ichimliklar', 'unit': 'piece',
            'batches': [
                {'purchase_price': 1000, 'selling_price': 1500, 'quantity': 120, 'days_to_expire': 365}
            ]
        },
        {
            'barcode': '2004', 'name': 'Sharbat (1L)', 'category': 'Ichimliklar', 'unit': 'piece',
            'batches': [
                {'purchase_price': 8000, 'selling_price': 12000, 'quantity': 30, 'days_to_expire': 90}
            ]
        },
        {
            'barcode': '2005', 'name': 'Energetik ichimlik', 'category': 'Ichimliklar', 'unit': 'piece',
            'batches': [
                {'purchase_price': 6000, 'selling_price': 9000, 'quantity': 25, 'days_to_expire': 180}
            ]
        },

        # Uy-ro'zg'or buyumlari
        {
            'barcode': '3001', 'name': 'Sabun', 'category': 'Uy-ro\'zg\'or buyumlari', 'unit': 'piece',
            'batches': [
                {'purchase_price': 3000, 'selling_price': 4000, 'quantity': 50, 'days_to_expire': 730}
            ]
        },
        {
            'barcode': '3002', 'name': 'Shampon', 'category': 'Uy-ro\'zg\'or buyumlari', 'unit': 'piece',
            'batches': [
                {'purchase_price': 12000, 'selling_price': 18000, 'quantity': 30, 'days_to_expire': 365}
            ]
        },
        {
            'barcode': '3003', 'name': 'Tish cho\'tkasi', 'category': 'Uy-ro\'zg\'or buyumlari', 'unit': 'piece',
            'batches': [
                {'purchase_price': 5000, 'selling_price': 8000, 'quantity': 40, 'days_to_expire': 1000}
            ]
        },
        {
            'barcode': '3004', 'name': 'Kir yuvish kukuni (1kg)', 'category': 'Uy-ro\'zg\'or buyumlari', 'unit': 'kg',
            'batches': [
                {'purchase_price': 15000, 'selling_price': 22000, 'quantity': 20, 'days_to_expire': 730}
            ]
        },
        {
            'barcode': '3005', 'name': 'Idish yuvish vositasi', 'category': 'Uy-ro\'zg\'or buyumlari', 'unit': 'piece',
            'batches': [
                {'purchase_price': 8000, 'selling_price': 12000, 'quantity': 25, 'days_to_expire': 365}
            ]
        },

        # Maktab buyumlari
        {
            'barcode': '4001', 'name': 'Qalam (ko\'k)', 'category': 'Maktab buyumlari', 'unit': 'piece',
            'batches': [
                {'purchase_price': 1500, 'selling_price': 2500, 'quantity': 100, 'days_to_expire': 1000}
            ]
        },
        {
            'barcode': '4002', 'name': 'Daftar (48 varaq)', 'category': 'Maktab buyumlari', 'unit': 'piece',
            'batches': [
                {'purchase_price': 2000, 'selling_price': 3000, 'quantity': 80, 'days_to_expire': 1000}
            ]
        },
        {
            'barcode': '4003', 'name': 'Karandash', 'category': 'Maktab buyumlari', 'unit': 'piece',
            'batches': [
                {'purchase_price': 1000, 'selling_price': 1800, 'quantity': 60, 'days_to_expire': 1000}
            ]
        },
        {
            'barcode': '4004', 'name': 'O\'chirg\'ich', 'category': 'Maktab buyumlari', 'unit': 'piece',
            'batches': [
                {'purchase_price': 800, 'selling_price': 1500, 'quantity': 50, 'days_to_expire': 1000}
            ]
        },
        {
            'barcode': '4005', 'name': 'Chizg\'ich (30cm)', 'category': 'Maktab buyumlari', 'unit': 'piece',
            'batches': [
                {'purchase_price': 2500, 'selling_price': 4000, 'quantity': 30, 'days_to_expire': 1000}
            ]
        }
    ]

    category_dict = {cat.name: cat for cat in categories}
    created_products = []

    for product_data in products_data:
        # Mahsulotni yaratish yoki topish
        category = category_dict[product_data['category']]
        product, created = Product.objects.get_or_create(
            barcode=product_data['barcode'],
            defaults={
                'name': product_data['name'],
                'category': category,
                'unit': product_data['unit'],
                'created_by': admin_user
            }
        )

        if created:
            print(f"   ✅ {product.name} mahsuloti yaratildi")
        else:
            print(f"   ✅ {product.name} allaqachon mavjud")

        # Partiyalarni yaratish
        for i, batch_data in enumerate(product_data['batches']):
            batch_number = f"B{datetime.now().strftime('%Y%m%d')}{product.id:03d}{i + 1:02d}"
            arrival_date = datetime.now().date() - timedelta(days=i * 2)  # Har xil sanada kelgan
            expiry_date = arrival_date + timedelta(days=batch_data['days_to_expire'])

            batch, batch_created = ProductBatch.objects.get_or_create(
                product=product,
                batch_number=batch_number,
                defaults={
                    'purchase_price': Decimal(str(batch_data['purchase_price'])),
                    'selling_price': Decimal(str(batch_data['selling_price'])),
                    'initial_quantity': batch_data['quantity'],
                    'remaining_quantity': batch_data['quantity'],
                    'arrival_date': arrival_date,
                    'expiry_date': expiry_date,
                    'created_by': admin_user
                }
            )

            if batch_created:
                print(f"     📦 Partiya {batch_number} yaratildi ({batch_data['quantity']} dona)")

        created_products.append(product)

    return created_products


def create_sample_sales(products, users):
    """Namuna savdolar yaratish"""
    print("💰 Namuna savdolar yaratish...")

    import random
    from django.utils import timezone

    # Oxirgi 7 kun ichida savdolar yaratish
    for day in range(7):
        sale_date = timezone.now() - timedelta(days=day)

        # Har kun 3-8 ta savdo
        daily_sales = random.randint(3, 8)

        for sale_num in range(daily_sales):
            # Tasodifiy kassir tanlash
            cashier = random.choice([u for u in users if not u.is_superuser])

            # Savdo raqami
            sale_number = f"S{sale_date.strftime('%Y%m%d')}{sale_num + 1:03d}"

            # Tasodifiy mahsulotlar tanlash (1-5 ta)
            selected_products = random.sample(products, random.randint(1, 5))

            subtotal = Decimal('0')
            sale_items_data = []

            for product in selected_products:
                # Mavjud partiyalardan tanlash
                available_batches = product.batches.filter(remaining_quantity__gt=0)
                if not available_batches.exists():
                    continue

                batch = available_batches.first()  # FIFO
                quantity = random.randint(1, min(5, batch.remaining_quantity))

                item_total = batch.selling_price * quantity
                subtotal += item_total

                sale_items_data.append({
                    'product': product,
                    'batch': batch,
                    'quantity': quantity,
                    'unit_price': batch.selling_price,
                    'total_price': item_total
                })

            if not sale_items_data:
                continue

            # Savdoni yaratish
            tax_amount = subtotal * Decimal('0.12')
            total_amount = subtotal + tax_amount
            payment_method = random.choice(['cash', 'card'])

            if payment_method == 'cash':
                # Naqd to'lov uchun qaytim hisoblash
                payment_amount = total_amount + random.randint(0, 5) * 1000  # Yumaloq summa
                change_amount = payment_amount - total_amount
            else:
                payment_amount = total_amount
                change_amount = Decimal('0')

            sale = Sale.objects.create(
                sale_number=sale_number,
                cashier=cashier,
                total_amount=total_amount,
                tax_amount=tax_amount,
                payment_method=payment_method,
                payment_amount=payment_amount,
                change_amount=change_amount,
                created_at=sale_date
            )

            # Savdo elementlarini yaratish va stock yangilash
            for item_data in sale_items_data:
                SaleItem.objects.create(
                    sale=sale,
                    product=item_data['product'],
                    batch=item_data['batch'],
                    quantity=item_data['quantity'],
                    unit_price=item_data['unit_price'],
                    total_price=item_data['total_price']
                )

                # Batch stock yangilash
                batch = item_data['batch']
                batch.remaining_quantity -= item_data['quantity']
                batch.save()

            print(f"   💳 Savdo {sale_number} yaratildi ({total_amount:,.0f} so'm)")


def main():
    """Asosiy funksiya"""
    print("🚀 POS Tizimi ma'lumotlar bazasini sozlash boshlandi...\n")

    try:
        # 1. Foydalanuvchilar yaratish
        admin_user = create_superuser()
        staff_users = create_staff_users()
        all_users = [admin_user] + staff_users

        print()

        # 2. Kategoriyalar yaratish
        categories = create_categories()

        print()

        # 3. Mahsulotlar va partiyalar yaratish
        products = create_products_and_batches(categories, admin_user)

        print()

        # 4. Namuna savdolar yaratish
        create_sample_sales(products, all_users)

        print()
        print("✅ Ma'lumotlar bazasi muvaffaqiyatli sozlandi!")
        print("\n📊 Yaratilgan ma'lumotlar:")
        print(f"   👥 Foydalanuvchilar: {len(all_users)}")
        print(f"   📂 Kategoriyalar: {len(categories)}")
        print(f"   📦 Mahsulotlar: {len(products)}")
        print(f"   🏷️ Partiyalar: {sum(p.batches.count() for p in products)}")
        print(f"   💰 Savdolar: {Sale.objects.count()}")

        print("\n🔐 Kirish ma'lumotlari:")
        print("   Admin: admin / admin123")
        print("   Kassir: kassir1 / kassir123")
        print("   Kassir: kassir2 / kassir123")
        print("   Manager: manager1 / manager123")

        print("\n🌐 Tizimni ishga tushirish:")
        print("   python manage.py runserver")
        print("   http://127.0.0.1:8000/")

    except Exception as e:
        print(f"❌ Xatolik yuz berdi: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
