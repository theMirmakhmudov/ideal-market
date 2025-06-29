from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Sum, Count, Q, F
from django.utils import timezone
from datetime import datetime, timedelta
import json
from .models import Product, Category, Sale, SaleItem, ReturnSale, ReturnItem, ProductBatch

def is_admin(user):
    return user.is_staff or user.is_superuser

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Noto\'g\'ri foydalanuvchi nomi yoki parol!')
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def dashboard(request):
    if request.user.is_staff:
        return redirect('admin_dashboard')
    else:
        return redirect('cashier_dashboard')

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    today = timezone.now().date()
    total_products = Product.objects.count()
    low_stock_products = []
    all_products = Product.objects.all()
    for product in all_products:
        total_remaining = product.batches.filter(
            remaining_quantity__gt=0,
            expiry_date__gte=today
        ).aggregate(total=Sum('remaining_quantity'))['total'] or 0
        if total_remaining > 0 and total_remaining < 10:
            low_stock_products.append(product)
    low_stock_count = len(low_stock_products)
    expired_batches = ProductBatch.objects.filter(
        expiry_date__lt=today,
        remaining_quantity__gt=0
    )
    expired_products_count = expired_batches.count()
    expired_product_ids = expired_batches.values_list('product_id', flat=True).distinct()
    expired_products_list = Product.objects.filter(id__in=expired_product_ids)
    today_sales = Sale.objects.filter(
        created_at__date=today
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    expiring_soon_count = ProductBatch.objects.filter(
        expiry_date__gte=today,
        expiry_date__lte=today + timedelta(days=7),
        remaining_quantity__gt=0
    ).count()
    week_start = today - timedelta(days=7)
    week_sales = Sale.objects.filter(
        created_at__date__gte=week_start
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    month_start = today.replace(day=1)
    month_sales = Sale.objects.filter(
        created_at__date__gte=month_start
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    context = {
        'total_products': total_products,
        'low_stock_products': low_stock_count,
        'low_stock_products_list': low_stock_products[:5],
        'expired_products': expired_products_count,
        'expired_products_list': expired_products_list[:5],
        'today_sales': today_sales,
        'week_sales': week_sales,
        'month_sales': month_sales,
        'expiring_soon_count': expiring_soon_count,
    }
    return render(request, 'admin_dashboard.html', context)

@login_required
def cashier_dashboard(request):
    products = Product.objects.filter(
        batches__remaining_quantity__gt=0,
        batches__expiry_date__gte=timezone.now().date()
    ).distinct()
    categories = Category.objects.all()
    products_json = []
    for product in products:
        products_json.append({
            'id': product.id,
            'name': product.name,
            'price': float(product.current_selling_price),
            'stock': product.total_stock,
            'category': product.category.name.lower(),
            'barcode': product.barcode,
            'unit': product.get_unit_display(),
            'image_url': product.image_url
        })
    context = {
        'products': products,
        'products_json': json.dumps(products_json),
        'categories': categories,
    }
    return render(request, 'cashier_dashboard.html', context)

@login_required
@user_passes_test(is_admin)
def product_list(request):
    products = Product.objects.all().order_by('-created_at').prefetch_related('batches', 'category')
    categories = Category.objects.all()
    category_filter = request.GET.get('category')
    search_query = request.GET.get('search')
    today = timezone.now().date()
    if category_filter:
        products = products.filter(category_id=category_filter)
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) | Q(barcode__icontains=search_query)
        )
    products_data = []
    for product in products:
        latest_batch = product.batches.order_by('-created_at').first()
        nearest_batch = product.batches.filter(remaining_quantity__gt=0).order_by('expiry_date').first()
        total_stock = product.batches.filter(remaining_quantity__gt=0).aggregate(
            total=Sum('remaining_quantity'))['total'] or 0
        products_data.append({
            'product': product,
            'latest_batch': latest_batch,
            'nearest_batch': nearest_batch,
            'total_stock': total_stock,
        })
    context = {
        'products_data': products_data,
        'categories': categories,
        'selected_category': category_filter,
        'search_query': search_query,
        'today': today,
    }
    return render(request, 'product_list.html', context)

@login_required
@user_passes_test(is_admin)
def add_product(request):
    if request.method == 'POST':
        try:
            category = Category.objects.get(id=request.POST['category'])
            product, created = Product.objects.get_or_create(
                barcode=request.POST['barcode'],
                defaults={
                    'name': request.POST['name'],
                    'category': category,
                    'unit': request.POST['unit'],
                    'created_by': request.user
                }
            )
            if 'image' in request.FILES:
                product.image = request.FILES['image']
                product.save()
            batch_number = f"B{timezone.now().strftime('%Y%m%d%H%M%S')}"
            ProductBatch.objects.create(
                product=product,
                batch_number=batch_number,
                purchase_price=request.POST['purchase_price'],
                selling_price=request.POST['selling_price'],
                initial_quantity=int(request.POST['stock_quantity']),
                remaining_quantity=int(request.POST['stock_quantity']),
                arrival_date=request.POST['arrival_date'],
                expiry_date=request.POST['expiry_date'],
                created_by=request.user
            )
            if created:
                messages.success(request, 'Yangi mahsulot va partiya muvaffaqiyatli qo\'shildi!')
            else:
                messages.success(request, 'Mavjud mahsulotga yangi partiya qo\'shildi!')
            return redirect('product_list')
        except Exception as e:
            messages.error(request, f'Xatolik: {str(e)}')
    categories = Category.objects.all()
    return render(request, 'add_product.html', {'categories': categories})


@login_required
@user_passes_test(is_admin)
def edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    categories = Category.objects.all()

    # ENG SO'NGI BATCH (yoki birinchi, FIFO uchun moslang)
    batch = product.batches.order_by('-created_at').first()

    if request.method == 'POST':
        try:
            category = Category.objects.get(id=request.POST['category'])
            product.barcode = request.POST['barcode']
            product.name = request.POST['name']
            product.category = category
            product.unit = request.POST['unit']
            if 'image' in request.FILES:
                product.image = request.FILES['image']
            product.save()
            # Batch yangilash
            if batch:
                batch.purchase_price = request.POST['purchase_price']
                batch.selling_price = request.POST['selling_price']
                batch.remaining_quantity = request.POST['stock_quantity']
                batch.arrival_date = request.POST['arrival_date']
                batch.expiry_date = request.POST['expiry_date']
                batch.save()
            messages.success(request, 'Mahsulot muvaffaqiyatli yangilandi!')
            return redirect('product_list')
        except Exception as e:
            messages.error(request, f'Xatolik: {str(e)}')

    context = {
        'product': product,
        'categories': categories,
        'batch': batch,  # ← Buni albatta yubor!
    }
    return render(request, 'edit_product.html', context)


@login_required
@user_passes_test(is_admin)
def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        product.delete()
        messages.success(request, 'Mahsulot o\'chirildi!')
    return redirect('product_list')

@login_required
def get_products_api(request):
    products = Product.objects.filter(
        batches__remaining_quantity__gt=0,
        batches__expiry_date__gte=timezone.now().date()
    ).distinct()
    products_data = []
    for product in products:
        products_data.append({
            'id': product.id,
            'name': product.name,
            'price': float(product.current_selling_price),
            'stock': product.total_stock,
            'category': product.category.name.lower(),
            'barcode': product.barcode,
            'unit': product.get_unit_display(),
            'image_url': product.image_url
        })
    return JsonResponse({'products': products_data})

@login_required
def search_product_by_barcode(request):
    barcode = request.GET.get('barcode', '')
    try:
        product = Product.objects.get(
            barcode=barcode,
            batches__remaining_quantity__gt=0,
            batches__expiry_date__gte=timezone.now().date()
        )
        return JsonResponse({
            'success': True,
            'product': {
                'id': product.id,
                'name': product.name,
                'price': float(product.current_selling_price),
                'stock': product.total_stock,
                'category': product.category.name.lower(),
                'barcode': product.barcode,
                'unit': product.get_unit_display(),
                'image_url': product.image_url
            }
        })
    except Product.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Mahsulot topilmadi'
        })

def allocate_stock_fifo(product, required_quantity):
    batches = product.batches.filter(
        remaining_quantity__gt=0,
        expiry_date__gte=timezone.now().date()
    ).order_by('arrival_date', 'created_at')
    allocated_items = []
    remaining_needed = required_quantity
    for batch in batches:
        if remaining_needed <= 0:
            break
        available = batch.remaining_quantity
        to_allocate = min(available, remaining_needed)
        allocated_items.append({
            'batch': batch,
            'quantity': to_allocate
        })
        remaining_needed -= to_allocate
    if remaining_needed > 0:
        return None
    return allocated_items

@login_required
def process_sale(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            cart_items = data.get('cart_items', [])
            payment_method = data.get('payment_method', 'cash')
            payment_amount = float(data.get('payment_amount', 0))
            if not cart_items:
                return JsonResponse({'success': False, 'error': 'Savat bo\'sh'})
            sale_number = f"S{timezone.now().strftime('%Y%m%d%H%M%S')}"
            allocated_stock = {}
            subtotal = 0
            for item in cart_items:
                try:
                    product = Product.objects.get(id=item['id'])
                    required_quantity = int(item['quantity'])
                    allocation = allocate_stock_fifo(product, required_quantity)
                    if not allocation:
                        return JsonResponse({
                            'success': False,
                            'error': f'{product.name} uchun omborda yetarli mahsulot yo\'q'
                        })
                    allocated_stock[product.id] = allocation
                    for alloc in allocation:
                        subtotal += float(alloc['batch'].selling_price) * alloc['quantity']
                except Product.DoesNotExist:
                    return JsonResponse({
                        'success': False,
                        'error': f'Mahsulot topilmadi (ID: {item["id"]})'
                    })
            tax_amount = subtotal * 0.12
            total_amount = subtotal + tax_amount
            change_amount = payment_amount - total_amount if payment_method == 'cash' else 0
            sale = Sale.objects.create(
                sale_number=sale_number,
                cashier=request.user,
                total_amount=total_amount,
                tax_amount=tax_amount,
                payment_method=payment_method,
                payment_amount=payment_amount,
                change_amount=change_amount
            )
            for product_id, allocation in allocated_stock.items():
                product = Product.objects.get(id=product_id)
                for alloc in allocation:
                    batch = alloc['batch']
                    quantity = alloc['quantity']
                    SaleItem.objects.create(
                        sale=sale,
                        product=product,
                        batch=batch,
                        quantity=quantity,
                        unit_price=batch.selling_price,
                        total_price=batch.selling_price * quantity
                    )
                    batch.remaining_quantity -= quantity
                    batch.save()
            return JsonResponse({
                'success': True,
                'sale_id': sale.id,
                'sale_number': sale_number,
                'total_amount': float(total_amount),
                'change_amount': float(change_amount),
                'subtotal': float(subtotal),
                'tax_amount': float(tax_amount),
                'payment_amount': float(payment_amount)
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def search_sale_by_number(request):
    sale_number = request.GET.get('sale_number', '')
    try:
        sale = Sale.objects.get(sale_number=sale_number)
        sale_items = []
        for item in sale.items.all():
            if item.remaining_quantity > 0:
                sale_items.append({
                    'id': item.id,
                    'product_id': item.product.id,
                    'product_name': item.product.name,
                    'quantity': item.quantity,
                    'returned_quantity': item.returned_quantity,
                    'remaining_quantity': item.remaining_quantity,
                    'unit_price': float(item.unit_price),
                    'total_price': float(item.total_price),
                    'unit': item.product.get_unit_display(),
                    'batch_number': item.batch.batch_number
                })
        return JsonResponse({
            'success': True,
            'sale': {
                'id': sale.id,
                'sale_number': sale.sale_number,
                'total_amount': float(sale.total_amount),
                'payment_method': sale.payment_method,
                'created_at': sale.created_at.strftime('%Y-%m-%d %H:%M'),
                'cashier': sale.cashier.get_full_name() or sale.cashier.username,
                'status': sale.status,
                'items': sale_items
            }
        })
    except Sale.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Chek topilmadi'
        })

@login_required
def process_return(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            sale_id = data.get('sale_id')
            return_items = data.get('return_items', [])
            reason = data.get('reason', '')
            if not return_items:
                return JsonResponse({'success': False, 'error': 'Qaytariladigan mahsulot tanlanmagan'})
            sale = Sale.objects.get(id=sale_id)
            return_number = f"R{timezone.now().strftime('%Y%m%d%H%M%S')}"
            total_return_amount = 0
            return_sale = ReturnSale.objects.create(
                original_sale=sale,
                return_number=return_number,
                cashier=request.user,
                total_return_amount=0,
                reason=reason
            )
            for return_item_data in return_items:
                sale_item = SaleItem.objects.get(id=return_item_data['sale_item_id'])
                return_quantity = int(return_item_data['quantity'])
                if return_quantity > sale_item.remaining_quantity:
                    return JsonResponse({
                        'success': False,
                        'error': f'{sale_item.product.name} uchun qaytarish miqdori juda ko\'p'
                    })
                return_amount = sale_item.unit_price * return_quantity
                total_return_amount += return_amount
                ReturnItem.objects.create(
                    return_sale=return_sale,
                    sale_item=sale_item,
                    returned_quantity=return_quantity,
                    return_amount=return_amount
                )
                sale_item.returned_quantity += return_quantity
                sale_item.save()
                batch = sale_item.batch
                batch.remaining_quantity += return_quantity
                batch.save()
            return_sale.total_return_amount = total_return_amount
            return_sale.save()
            all_returned = all(item.remaining_quantity == 0 for item in sale.items.all())
            if all_returned:
                sale.status = 'returned'
            else:
                sale.status = 'partially_returned'
            sale.save()
            return JsonResponse({
                'success': True,
                'return_number': return_number,
                'total_return_amount': float(total_return_amount)
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
@user_passes_test(is_admin)
def statistics(request):
    today = timezone.now().date()
    total_products = Product.objects.count()
    expired_batches = ProductBatch.objects.filter(
        expiry_date__lt=today,
        remaining_quantity__gt=0
    ).select_related('product')
    expired_products = []
    for batch in expired_batches:
        days_expired = (today - batch.expiry_date).days
        loss_amount = float(batch.purchase_price) * batch.remaining_quantity
        expired_products.append({
            'name': batch.product.name,
            'expiry_date': batch.expiry_date,
            'days_expired': days_expired,
            'stock_quantity': batch.remaining_quantity,
            'loss_amount': loss_amount,
            'batch_number': batch.batch_number,
            'unit': batch.product.get_unit_display()
        })
    expiring_soon_count = ProductBatch.objects.filter(
        expiry_date__gte=today,
        expiry_date__lte=today + timedelta(days=7),
        remaining_quantity__gt=0
    ).count()
    low_stock_products = Product.objects.filter(
        batches__remaining_quantity__lt=10,
        batches__remaining_quantity__gt=0
    ).distinct()
    low_stock_count = low_stock_products.count()
    total_inventory_value = ProductBatch.objects.filter(
        remaining_quantity__gt=0
    ).aggregate(
        total=Sum(F('purchase_price') * F('remaining_quantity'))
    )['total'] or 0
    category_stats = Category.objects.annotate(
        count=Count('product')
    ).order_by('-count')
    today_sales = Sale.objects.filter(
        created_at__date=today
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    this_month = today.replace(day=1)
    monthly_revenue = Sale.objects.filter(
        created_at__date__gte=this_month
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    new_products_this_month = Product.objects.filter(
        created_at__date__gte=this_month
    ).count()
    top_selling_products = SaleItem.objects.values('product__name').annotate(
        sold_quantity=Sum('quantity')
    ).order_by('-sold_quantity')[:5]
    week_start = today - timedelta(days=7)
    week_sales = Sale.objects.filter(created_at__date__gte=week_start)
    week_revenue = week_sales.aggregate(total=Sum('total_amount'))['total'] or 0
    prev_week_start = week_start - timedelta(days=7)
    prev_week_revenue = Sale.objects.filter(
        created_at__date__gte=prev_week_start,
        created_at__date__lt=week_start
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    sales_growth = 0
    if prev_week_revenue > 0:
        sales_growth = round(((week_revenue - prev_week_revenue) / prev_week_revenue) * 100, 1)
    daily_sales = []
    for i in range(30):
        date = today - timedelta(days=i)
        daily_revenue = Sale.objects.filter(created_at__date=date).aggregate(
            total=Sum('total_amount'))['total'] or 0
        daily_sales.append({
            'date': date.strftime('%Y-%m-%d'),
            'revenue': float(daily_revenue)
        })
    daily_sales.reverse()
    context = {
        'total_products': total_products,
        'expired_products': expired_products,
        'expired_products_count': len(expired_products),
        'expiring_soon_count': expiring_soon_count,
        'low_stock_count': low_stock_count,
        'total_inventory_value': total_inventory_value,
        'today_sales': today_sales,
        'monthly_revenue': monthly_revenue,
        'week_revenue': week_revenue,
        'sales_growth': sales_growth,
        'new_products_this_month': new_products_this_month,
        'category_stats': category_stats,
        'top_selling_products': top_selling_products,
        'low_stock_products': low_stock_products,
        'daily_sales': json.dumps(daily_sales),
        'today_revenue': today_sales,
        'today_sales_count': Sale.objects.filter(created_at__date=today).count(),
        'month_revenue': monthly_revenue,
        'top_products': SaleItem.objects.values('product__name').annotate(
            total_sold=Sum('quantity'),
            total_revenue=Sum('total_price')
        ).order_by('-total_sold')[:10],
        'expired_batches': expired_batches,
    }
    return render(request, 'statistics.html', context)

@login_required
@user_passes_test(is_admin)
def add_category(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        if name:
            Category.objects.create(name=name)
            messages.success(request, 'Kategoriya qo\'shildi!')
        return redirect('product_list')
    return render(request, 'add_category.html')

def standalone_pos(request):
    return render(request, 'standalone_pos.html')
