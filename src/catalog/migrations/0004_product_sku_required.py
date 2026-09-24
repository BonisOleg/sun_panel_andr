from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0003_delivery_phase1"),
    ]

    operations = [
        migrations.AlterField(
            model_name="product",
            name="sku",
            field=models.CharField(max_length=64, verbose_name="SKU"),
        ),
        migrations.AddConstraint(
            model_name="product",
            constraint=models.CheckConstraint(
                condition=~models.Q(sku=""),
                name="catalog_product_sku_not_blank",
            ),
        ),
    ]
