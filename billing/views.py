from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.db.models import Count, Q, Sum
from django.db.models.deletion import ProtectedError
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils import timezone

from .models import Bill, BillItem, Category, Customer, Product


TAX_CHOICES = [Decimal("0"), Decimal("5"), Decimal("10"), Decimal("18")]


def get_bill_with_items(bill_id):
    """Return a bill with customer and items loaded."""

    return get_object_or_404(
        Bill.objects.select_related("customer", "category").prefetch_related("items__product__category"),
        id=bill_id,
    )


def get_bill_context(bill):
    """Build shared template context for invoice pages."""

    return {
        "page_title": "Bill Summary",
        "bill": bill,
        "items": bill.items.all(),
    }


def generate_bill_number():
    """Create a readable and unique bill number for demo use."""

    timestamp = timezone.now().strftime("%Y%m%d%H%M%S%f")
    return f"BILL-{timestamp}"


def parse_decimal(value):
    """Safely convert posted text into Decimal."""

    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None


def dashboard(request):
    total_customers = Customer.objects.count()
    total_products = Product.objects.count()
    total_bills = Bill.objects.count()
    total_revenue = Bill.objects.aggregate(total=Sum("total_amount"))["total"] or Decimal("0.00")
    total_categories = Category.objects.count()
    recent_bills = Bill.objects.select_related("customer", "category").prefetch_related("items")[:5]

    context = {
        "page_title": "Dashboard",
        "total_customers": total_customers,
        "total_products": total_products,
        "total_bills": total_bills,
        "total_categories": total_categories,
        "total_revenue": total_revenue,
        "recent_bills": recent_bills,
    }
    return render(request, "billing/dashboard.html", context)


def categories(request):
    query = request.GET.get("q", "").strip()
    edit_id = request.GET.get("edit", "").strip()
    category_list = Category.objects.annotate(
        total_products=Count("products", distinct=True),
        total_bills=Count("bills", distinct=True),
    )

    if query:
        category_list = category_list.filter(name__icontains=query)

    editing_category = None
    if edit_id:
        editing_category = Category.objects.filter(id=edit_id).first()

    context = {
        "page_title": "Categories",
        "categories": category_list,
        "query": query,
        "editing_category": editing_category,
    }
    return render(request, "billing/categories.html", context)


def add_category(request):
    if request.method == "POST":
        name = request.POST.get("name", "").strip()

        if not name:
            messages.error(request, "Please enter a category name.")
        elif Category.objects.filter(name__iexact=name).exists():
            messages.error(request, "This category already exists.")
        else:
            Category.objects.create(name=name)
            messages.success(request, "Category added successfully.")

    return redirect("billing:categories")


def edit_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)

    if request.method == "POST":
        name = request.POST.get("name", "").strip()

        if not name:
            messages.error(request, "Please enter a category name.")
        elif Category.objects.exclude(id=category.id).filter(name__iexact=name).exists():
            messages.error(request, "This category already exists.")
        else:
            category.name = name
            category.save()
            messages.success(request, "Category updated successfully.")

    return redirect("billing:categories")


def delete_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)

    if request.method == "POST":
        try:
            category.delete()
            messages.success(request, "Category deleted successfully.")
        except ProtectedError:
            messages.error(
                request,
                "This category is already used in products or bills and cannot be deleted.",
            )

    return redirect("billing:categories")


def customers(request):
    query = request.GET.get("q", "").strip()
    customer_list = Customer.objects.all()

    if query:
        customer_list = customer_list.filter(
            Q(name__icontains=query)
            | Q(phone__icontains=query)
            | Q(email__icontains=query)
            | Q(address__icontains=query)
        )

    context = {
        "page_title": "Customers",
        "customers": customer_list,
        "query": query,
    }
    return render(request, "billing/customers.html", context)


def add_customer(request):
    customer_data = {"name": "", "phone": "", "email": "", "address": ""}

    if request.method == "POST":
        customer_data = {
            "name": request.POST.get("name", "").strip(),
            "phone": request.POST.get("phone", "").strip(),
            "email": request.POST.get("email", "").strip(),
            "address": request.POST.get("address", "").strip(),
        }

        if not customer_data["name"] or not customer_data["phone"] or not customer_data["address"]:
            messages.error(request, "Please fill in name, phone, and address.")
        else:
            Customer.objects.create(**customer_data)
            messages.success(request, "Customer added successfully.")
            return redirect("billing:customers")

    context = {
        "page_title": "Add Customer",
        "button_label": "Save Customer",
        "customer": customer_data,
        "is_edit": False,
    }
    return render(request, "billing/add_customer.html", context)


def edit_customer(request, customer_id):
    customer = get_object_or_404(Customer, id=customer_id)

    if request.method == "POST":
        customer.name = request.POST.get("name", "").strip()
        customer.phone = request.POST.get("phone", "").strip()
        customer.email = request.POST.get("email", "").strip()
        customer.address = request.POST.get("address", "").strip()

        if not customer.name or not customer.phone or not customer.address:
            messages.error(request, "Please fill in name, phone, and address.")
        else:
            customer.save()
            messages.success(request, "Customer updated successfully.")
            return redirect("billing:customers")

    context = {
        "page_title": "Edit Customer",
        "button_label": "Update Customer",
        "customer": customer,
        "is_edit": True,
    }
    return render(request, "billing/add_customer.html", context)


def delete_customer(request, customer_id):
    customer = get_object_or_404(Customer, id=customer_id)

    if request.method == "POST":
        customer.delete()
        messages.success(request, "Customer deleted successfully.")

    return redirect("billing:customers")


def products(request):
    query = request.GET.get("q", "").strip()
    category = request.GET.get("category", "").strip()
    product_list = Product.objects.select_related("category").all()
    category_list = Category.objects.all()

    if query:
        product_list = product_list.filter(
            Q(name__icontains=query)
            | Q(description__icontains=query)
            | Q(category__name__icontains=query)
        )

    if category:
        product_list = product_list.filter(category_id=category)

    context = {
        "page_title": "Products & Services",
        "products": product_list,
        "query": query,
        "selected_category": category,
        "categories": category_list,
    }
    return render(request, "billing/products.html", context)


def add_product(request):
    category_list = Category.objects.all()
    product_data = {"name": "", "category": "", "price": "", "description": ""}

    if request.method == "POST":
        product_data = {
            "name": request.POST.get("name", "").strip(),
            "category": request.POST.get("category", "").strip(),
            "price": request.POST.get("price", "").strip(),
            "description": request.POST.get("description", "").strip(),
        }

        price = parse_decimal(product_data["price"])
        category_obj = Category.objects.filter(id=product_data["category"]).first()

        if not product_data["name"] or price is None:
            messages.error(request, "Please enter a valid product name and price.")
        elif price <= 0:
            messages.error(request, "Price must be greater than zero.")
        elif category_obj is None:
            messages.error(request, "Please choose a valid category.")
        else:
            Product.objects.create(
                name=product_data["name"],
                category=category_obj,
                price=price,
                description=product_data["description"],
            )
            messages.success(request, "Product or service added successfully.")
            return redirect("billing:products")

    context = {
        "page_title": "Add Product",
        "button_label": "Save Product",
        "product": product_data,
        "categories": category_list,
        "is_edit": False,
    }
    return render(request, "billing/add_product.html", context)


def edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    category_list = Category.objects.all()

    if request.method == "POST":
        product.name = request.POST.get("name", "").strip()
        product.description = request.POST.get("description", "").strip()
        category_id = request.POST.get("category", "").strip()
        price = parse_decimal(request.POST.get("price", "").strip())
        category_obj = Category.objects.filter(id=category_id).first()

        if not product.name or price is None:
            messages.error(request, "Please enter a valid product name and price.")
        elif price <= 0:
            messages.error(request, "Price must be greater than zero.")
        elif category_obj is None:
            messages.error(request, "Please choose a valid category.")
        else:
            product.category = category_obj
            product.price = price
            product.save()
            messages.success(request, "Product updated successfully.")
            return redirect("billing:products")

    context = {
        "page_title": "Edit Product",
        "button_label": "Update Product",
        "product": product,
        "categories": category_list,
        "is_edit": True,
    }
    return render(request, "billing/add_product.html", context)


def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == "POST":
        product.delete()
        messages.success(request, "Product deleted successfully.")

    return redirect("billing:products")


def create_bill(request):
    customer_list = Customer.objects.all()
    product_list = Product.objects.select_related("category").all()
    category_list = Category.objects.all()
    selected_quantities = {}
    selected_customer = request.POST.get("customer", "")
    selected_category = request.POST.get("category", "")
    selected_tax = request.POST.get("tax_percentage", "5")

    if request.method == "POST":
        customer = Customer.objects.filter(id=selected_customer).first()
        bill_category = Category.objects.filter(id=selected_category).first()
        tax_percentage = parse_decimal(selected_tax)
        bill_items = []
        subtotal = Decimal("0.00")
        has_invalid_quantity = False

        for product in product_list:
            raw_quantity = request.POST.get(f"quantity_{product.id}", "").strip()
            selected_quantities[str(product.id)] = raw_quantity

            if not raw_quantity:
                continue

            try:
                quantity = int(raw_quantity)
            except ValueError:
                has_invalid_quantity = True
                continue

            if quantity < 0:
                has_invalid_quantity = True
                continue

            if quantity == 0:
                continue

            line_total = product.price * quantity
            subtotal += line_total
            bill_items.append({
                "product": product,
                "quantity": quantity,
                "price": product.price,
            })

        if customer is None:
            messages.error(request, "Please select a valid customer.")
        elif bill_category is None:
            messages.error(request, "Please choose a valid billing category.")
        elif tax_percentage is None or tax_percentage < 0:
            messages.error(request, "Please choose a valid tax percentage.")
        elif has_invalid_quantity:
            messages.error(request, "Quantities must be whole numbers greater than or equal to zero.")
        elif not bill_items:
            messages.error(request, "Please add at least one product or service to the bill.")
        else:
            tax_amount = (subtotal * tax_percentage / Decimal("100")).quantize(Decimal("0.01"))
            final_total = (subtotal + tax_amount).quantize(Decimal("0.01"))
            bill = Bill.objects.create(
                bill_number=generate_bill_number(),
                customer=customer,
                category=bill_category,
                subtotal_amount=subtotal.quantize(Decimal("0.01")),
                tax_percentage=tax_percentage.quantize(Decimal("0.01")),
                tax_amount=tax_amount,
                total_amount=final_total,
            )

            for item in bill_items:
                BillItem.objects.create(
                    bill=bill,
                    product=item["product"],
                    quantity=item["quantity"],
                    price=item["price"],
                )

            messages.success(request, "Bill generated successfully.")
            return redirect("billing:bill_summary", bill_id=bill.id)

    context = {
        "page_title": "Create Bill",
        "customers": customer_list,
        "products": product_list,
        "categories": category_list,
        "tax_choices": TAX_CHOICES,
        "selected_customer": str(selected_customer),
        "selected_category": selected_category,
        "selected_tax": str(selected_tax),
        "selected_quantities": selected_quantities,
    }
    return render(request, "billing/create_bill.html", context)


def bill_summary(request, bill_id):
    bill = get_bill_with_items(bill_id)
    context = get_bill_context(bill)
    return render(request, "billing/bill_summary.html", context)


def download_invoice(request, bill_id):
    """Download the invoice as a standalone HTML file without extra packages."""

    bill = get_bill_with_items(bill_id)
    context = get_bill_context(bill)
    html_content = render_to_string("billing/invoice_download.html", context, request=request)
    response = HttpResponse(html_content, content_type="text/html; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{bill.bill_number.lower()}.html"'
    return response
