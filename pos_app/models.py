from django.db import models
from django.contrib.auth.models import User


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Kategoriya nomi")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Kategoriya"
        verbose_name_plural = "Kategoriyalar"


class Product(models.Model):
    UNIT_CHOICES = [
        ('kg', 'Kilogram'),
        ('piece', 'Dona'),
        ('liter', 'Litr'),
        ('meter', 'Metr'),
    ]

    barcode = models.CharField(max_length=50, unique=True, verbose_name="Shtrix kod")
    name = models.CharField(max_length=200, verbose_name="Mahsulot nomi")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name="Kategoriya")
    image = models.ImageField(upload_to='products/', blank=True, null=True, verbose_name="Mahsulot rasmi")
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES, default='piece', verbose_name="O'lchov birligi")
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Yaratuvchi")

    def __str__(self):
        return f"{self.name} - {self.barcode}"

    @property
    def current_selling_price(self):
        """Eng oxirgi batch narxi"""
        latest_batch = self.batches.filter(remaining_quantity__gt=0).order_by('-created_at').first()
        return latest_batch.selling_price if latest_batch else 0

    @property
    def total_stock(self):
        """Jami ombor miqdori"""
        return self.batches.filter(remaining_quantity__gt=0).aggregate(
            total=models.Sum('remaining_quantity'))['total'] or 0

    @property
    def image_url(self):
        """Rasm URL ini qaytarish"""
        if self.image:
            return self.image.url
        return None

    class Meta:
        verbose_name = "Mahsulot"
        verbose_name_plural = "Mahsulotlar"
        ordering = ['-created_at']


class ProductBatch(models.Model):
    """Mahsulot partiyalari - har bir qo'shilgan mahsulot alohida batch"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='batches', verbose_name="Mahsulot")
    batch_number = models.CharField(max_length=50, verbose_name="Partiya raqami")
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Sotib olish narxi")
    selling_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Sotuv narxi")
    initial_quantity = models.IntegerField(verbose_name="Boshlang'ich miqdor")
    remaining_quantity = models.IntegerField(verbose_name="Qolgan miqdor")
    arrival_date = models.DateField(verbose_name="Kelgan sana")
    expiry_date = models.DateField(verbose_name="Yaroqlilik muddati")
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Yaratuvchi")

    def __str__(self):
        return f"{self.product.name} - {self.batch_number} ({self.remaining_quantity}/{self.initial_quantity})"

    @property
    def sold_quantity(self):
        return self.initial_quantity - self.remaining_quantity

    class Meta:
        verbose_name = "Mahsulot partiyasi"
        verbose_name_plural = "Mahsulot partiyalari"
        ordering = ['arrival_date', 'created_at']  # FIFO uchun


class Sale(models.Model):
    PAYMENT_METHODS = [
        ('cash', 'Naqd'),
        ('card', 'Karta'),
    ]

    STATUS_CHOICES = [
        ('completed', 'Yakunlangan'),
        ('returned', 'Qaytarilgan'),
        ('partially_returned', 'Qisman qaytarilgan'),
    ]

    sale_number = models.CharField(max_length=50, unique=True, verbose_name="Savdo raqami")
    cashier = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Kassir")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Umumiy summa")
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Soliq miqdori")
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHODS, verbose_name="To'lov usuli")
    payment_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="To'langan summa")
    change_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Qaytim")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='completed', verbose_name="Holati")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan vaqt")

    def __str__(self):
        return f"Savdo #{self.sale_number} - {self.total_amount} so'm"

    class Meta:
        verbose_name = "Savdo"
        verbose_name_plural = "Savdolar"
        ordering = ['-created_at']


class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items', verbose_name="Savdo")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Mahsulot")
    batch = models.ForeignKey(ProductBatch, on_delete=models.CASCADE, verbose_name="Partiya")
    quantity = models.IntegerField(verbose_name="Miqdori")
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Birlik narxi")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Umumiy narx")
    returned_quantity = models.IntegerField(default=0, verbose_name="Qaytarilgan miqdor")

    def __str__(self):
        return f"{self.product.name} x {self.quantity} ({self.batch.batch_number})"

    @property
    def remaining_quantity(self):
        return self.quantity - self.returned_quantity

    class Meta:
        verbose_name = "Savdo elementi"
        verbose_name_plural = "Savdo elementlari"


class ReturnSale(models.Model):
    original_sale = models.ForeignKey(Sale, on_delete=models.CASCADE, verbose_name="Asl savdo")
    return_number = models.CharField(max_length=50, unique=True, verbose_name="Qaytarish raqami")
    cashier = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Kassir")
    total_return_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Qaytarilgan summa")
    reason = models.TextField(blank=True, verbose_name="Qaytarish sababi")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Qaytarilgan vaqt")

    def __str__(self):
        return f"Qaytarish #{self.return_number}"

    class Meta:
        verbose_name = "Qaytarish"
        verbose_name_plural = "Qaytarishlar"
        ordering = ['-created_at']


class ReturnItem(models.Model):
    return_sale = models.ForeignKey(ReturnSale, on_delete=models.CASCADE, related_name='items')
    sale_item = models.ForeignKey(SaleItem, on_delete=models.CASCADE)
    returned_quantity = models.IntegerField(verbose_name="Qaytarilgan miqdor")
    return_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Qaytarilgan summa")

    def __str__(self):
        return f"{self.sale_item.product.name} x {self.returned_quantity}"

    class Meta:
        verbose_name = "Qaytarish elementi"
        verbose_name_plural = "Qaytarish elementlari"
