from django.db import migrations, models
import django.db.models.deletion


def create_default_categories(apps, schema_editor):
    Category = apps.get_model("billing", "Category")
    default_names = [
        "Business",
        "Health",
        "Science",
        "Sports",
        "Entertainment",
        "Technology",
        "General",
    ]
    for name in default_names:
        Category.objects.get_or_create(name=name)


def move_existing_categories(apps, schema_editor):
    Category = apps.get_model("billing", "Category")
    Product = apps.get_model("billing", "Product")
    Bill = apps.get_model("billing", "Bill")

    label_map = {
        "business": "Business",
        "health": "Health",
        "science": "Science",
        "sports": "Sports",
        "entertainment": "Entertainment",
        "technology": "Technology",
        "general": "General",
    }

    for product in Product.objects.all():
        category_name = label_map.get(product.category, product.category.title())
        category = Category.objects.get(name=category_name)
        product.category_new_id = category.id
        product.save(update_fields=["category_new"])

    for bill in Bill.objects.all():
        category_name = label_map.get(bill.category, bill.category.title())
        category = Category.objects.get(name=category_name)
        bill.category_new_id = category.id
        bill.save(update_fields=["category_new"])


class Migration(migrations.Migration):

    dependencies = [
        ("billing", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Category",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100, unique=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "verbose_name_plural": "Categories",
                "ordering": ["name"],
            },
        ),
        migrations.RunPython(create_default_categories, migrations.RunPython.noop),
        migrations.AddField(
            model_name="product",
            name="category_new",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="products", to="billing.category"),
        ),
        migrations.AddField(
            model_name="bill",
            name="category_new",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="bills", to="billing.category"),
        ),
        migrations.RunPython(move_existing_categories, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="product",
            name="category",
        ),
        migrations.RemoveField(
            model_name="bill",
            name="category",
        ),
        migrations.RenameField(
            model_name="product",
            old_name="category_new",
            new_name="category",
        ),
        migrations.RenameField(
            model_name="bill",
            old_name="category_new",
            new_name="category",
        ),
        migrations.AlterField(
            model_name="product",
            name="category",
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="products", to="billing.category"),
        ),
        migrations.AlterField(
            model_name="bill",
            name="category",
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="bills", to="billing.category"),
        ),
    ]
