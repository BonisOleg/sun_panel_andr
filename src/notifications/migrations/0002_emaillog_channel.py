from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("notifications", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="emaillog",
            name="channel",
            field=models.CharField(
                choices=[("email", "Email"), ("telegram", "Telegram")],
                default="email",
                max_length=16,
            ),
        ),
        migrations.AlterField(
            model_name="emaillog",
            name="to_email",
            field=models.CharField(
                blank=True,
                default="",
                help_text="Email або Telegram chat_id",
                max_length=255,
                verbose_name="Отримувач",
            ),
        ),
        migrations.AlterModelOptions(
            name="emaillog",
            options={
                "ordering": ["-created_at"],
                "verbose_name": "Лог сповіщення",
                "verbose_name_plural": "Логи сповіщень",
            },
        ),
    ]
