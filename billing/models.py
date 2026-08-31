from decimal import Decimal

from django.db import models
from django.db.models import PROTECT
from django.utils import timezone


DEFAULT_CATEGORY_NAMES = [
    "Business",
    "Health",
    "Science",
    "Sports",
    "Entertainment",
    "Technology",
    "General",
]


class Category(models.Model):
    """Stores billing categories that users can manage dynamically."""

    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


class Customer(models.Model):
    """Stores customer details used while generating bills."""

    name = models.CharField(max_length=120)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    address = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Product(models.Model):
    """Stores products or services that can be billed."""

    name = models.CharField(max_length=120)
    category = models.ForeignKey(Category, on_delete=PROTECT, related_name="products")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Bill(models.Model):
    """Stores the main bill header information."""

    bill_number = models.CharField(max_length=30, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="bills")
    category = models.ForeignKey(Category, on_delete=PROTECT, related_name="bills")
    date = models.DateTimeField(default=timezone.now)
    subtotal_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    tax_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("5.00"))
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return self.bill_number

    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())


class BillItem(models.Model):
    """Stores individual line items for each bill."""

    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"

    @property
    def line_total(self):
        return self.price * self.quantity
