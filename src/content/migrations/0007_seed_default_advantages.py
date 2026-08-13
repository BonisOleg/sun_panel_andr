from django.db import migrations

DEFAULTS = (
    ("Висока якість", "Обладнання перевірених виробників для стабільної роботи станції."),
    ("Швидка доставка", "Комплектація та відправка під ваш обʼєкт у зручні терміни."),
    ("Гарантія", "Офіційна гарантія та підтримка після покупки."),
    ("Експертна консультація", "Допоможемо підібрати панелі та кріплення під задачу."),
)


def seed_advantages(apps, schema_editor):
    HomeAdvantage = apps.get_model("content", "HomeAdvantage")
    if HomeAdvantage.objects.exists():
        return
    for i, (title, text) in enumerate(DEFAULTS):
        HomeAdvantage.objects.create(
            title=title,
            text=text,
            sort_order=i,
            is_active=True,
        )


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("content", "0006_homepage_singleton_and_footer_socials"),
    ]

    operations = [
        migrations.RunPython(seed_advantages, noop),
    ]
