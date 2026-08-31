from django.contrib import admin

from .models import Bill, BillItem, Category, Customer, Product


class BillItemInline(admin.TabularInline):
    model = BillItem
    extra = 0


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("name", "phone", "email")
    search_fields = ("name", "phone", "email")


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at")
    search_fields = ("name",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price")
    list_filter = ("category",)
    search_fields = ("name", "description", "category__name")


@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    list_display = ("bill_number", "customer", "category", "date", "total_amount")
    list_filter = ("category", "date")
    search_fields = ("bill_number", "customer__name", "category__name")
    inlines = [BillItemInline]
