from django.urls import path

from . import views

app_name = "billing"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("categories/", views.categories, name="categories"),
    path("categories/add/", views.add_category, name="add_category"),
    path("categories/<int:category_id>/edit/", views.edit_category, name="edit_category"),
    path("categories/<int:category_id>/delete/", views.delete_category, name="delete_category"),
    path("customers/", views.customers, name="customers"),
    path("customers/add/", views.add_customer, name="add_customer"),
    path("customers/<int:customer_id>/edit/", views.edit_customer, name="edit_customer"),
    path("customers/<int:customer_id>/delete/", views.delete_customer, name="delete_customer"),
    path("products/", views.products, name="products"),
    path("products/add/", views.add_product, name="add_product"),
    path("products/<int:product_id>/edit/", views.edit_product, name="edit_product"),
    path("products/<int:product_id>/delete/", views.delete_product, name="delete_product"),
    path("bills/create/", views.create_bill, name="create_bill"),
    path("bills/<int:bill_id>/", views.bill_summary, name="bill_summary"),
    path("bills/<int:bill_id>/download/", views.download_invoice, name="download_invoice"),
]
