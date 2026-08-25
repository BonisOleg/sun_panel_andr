from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("commerce", "0002_delivery_phase1"),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="telegram_sent_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
