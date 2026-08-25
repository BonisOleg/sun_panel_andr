from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("content", "0011_site_settings_logo_footer_help"),
    ]

    operations = [
        migrations.AddField(
            model_name="contactlead",
            name="telegram_sent_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
