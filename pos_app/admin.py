from django.contrib import admin
from .models import (
    Category, Product, ProductBatch, Sale, SaleItem,
    ReturnSale, ReturnItem
)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']
    ordering = ['name']

class ProductBatchInline(admin.TabularInline):
    model = ProductBatch
    extra = 0
    readonly_fields = ['batch_number', 'created_at']

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'barcode', 'category', 'unit', 'created_at']
    list_filter = ['category', 'unit', 'created_at']
    search_fields = ['name', 'barcode']
    readonly_fields = ['created_at']
    inlines = [ProductBatchInline]

@admin.register(ProductBatch)
class ProductBatchAdmin(admin.ModelAdmin):
    list_display = ['batch_number', 'product', 'purchase_price', 'selling_price', 'remaining_quantity', 'arrival_date']
    list_filter = ['product__category', 'arrival_date', 'expiry_date']
    search_fields = ['batch_number', 'product__name']
    readonly_fields = ['batch_number', 'created_at']

class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 0
    readonly_fields = ['total_price']

@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ['sale_number', 'cashier', 'total_amount', 'payment_method', 'created_at']
    list_filter = ['payment_method', 'created_at', 'cashier']
    search_fields = ['sale_number']
    readonly_fields = ['sale_number', 'created_at']
    inlines = [SaleItemInline]

class ReturnItemInline(admin.TabularInline):
    model = ReturnItem
    extra = 0
    readonly_fields = ['return_amount']

@admin.register(ReturnSale)
class ReturnSaleAdmin(admin.ModelAdmin):
    list_display = ['return_number', 'original_sale', 'cashier', 'total_return_amount', 'created_at']
    list_filter = ['created_at', 'cashier']
    search_fields = ['return_number', 'original_sale__sale_number']
    readonly_fields = ['return_number', 'created_at']
    inlines = [ReturnItemInline]

# Admin site customization
admin.site.site_header = "POS Tizimi Boshqaruvi"
admin.site.site_title = "POS Admin"
admin.site.index_title = "POS Tizimi Boshqaruv Paneli"
