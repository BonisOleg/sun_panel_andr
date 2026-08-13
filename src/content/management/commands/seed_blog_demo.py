"""Seed demo blog posts for Soliron (list pagination + prose check)."""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path

from django.core.management.base import BaseCommand
from django.utils import timezone

from src.content.blog_cover_art import make_cover
from src.content.models import BlogPost

DEMO_SLUG_PREFIX = "demo-"

ARTICLES: list[dict] = [
    {
        "slug": "yak-obraty-sonyachni-paneli",
        "title": "Як обрати сонячні панелі для приватного будинку",
        "excerpt": "Короткий гайд: потужність, тип модулів, орієнтація даху та типові помилки при першому розрахунку.",
        "scene": "panels",
        "body": """
<p>Сонячна станція для дому починається не з покупки панелей, а з оцінки споживання та умов монтажу.</p>
<p>Перед замовленням обладнання варто зафіксувати:</p>
<ul>
  <li>середньомісячне споживання кВт·год;</li>
  <li>вільну площу даху або землі;</li>
  <li>орієнтацію та кут нахилу;</li>
  <li>обмеження мережі та лічильника.</li>
</ul>
<h2>Які панелі обрати</h2>
<p>Для більшості приватних обʼєктів оптимальні монокристалічні модулі з високим ККД. Вони краще працюють при обмеженій площі даху.</p>
<ol>
  <li>Визначте цільову потужність станції.</li>
  <li>Підберіть інвертор із запасом 10–20%.</li>
  <li>Закладіть якісне кріплення під тип покрівлі.</li>
</ol>
<p>Якщо потрібна консультація — зверніться до менеджера Soliron: допоможемо зібрати комплектацію під ваш обʼєкт.</p>
""",
    },
    {
        "slug": "mono-vs-poli-2026",
        "title": "Моно vs полі: що вигідніше у 2026",
        "excerpt": "Порівнюємо ефективність, ціну та поведінку модулів у хмарну погоду.",
        "scene": "mono_poly",
        "body": """
<p>Полікристалічні панелі майже зникли з ринку нових проєктів. Причина проста — монокристал дає більше енергії з того самого квадратного метра.</p>
<blockquote><p>На обмеженому даху кожен відсоток ККД напряму впливає на окупність.</p></blockquote>
<ul>
  <li><strong>Монокристал</strong> — вищий ККД, кращий вигляд, вища ціна.</li>
  <li><strong>Полікристал</strong> — дешевше, але потребує більше площі.</li>
</ul>
<p>Для нових станцій Soliron рекомендує сучасні мономодулі з гарантією виробника.</p>
""",
    },
    {
        "slug": "invertor-dlya-domashnoyi-ses",
        "title": "Інвертор для домашньої СЕС: на що дивитися",
        "excerpt": "ККД, кількість MPPT, захист і сервіс — критерії, які реально впливають на роботу станції.",
        "scene": "inverter",
        "body": """
<p>Інвертор — «мозок» станції. Саме він перетворює постійний струм панелей на змінний для мережі та дому.</p>
<h3>Ключові параметри</h3>
<ol>
  <li>Номінальна потужність і пікове навантаження.</li>
  <li>Кількість MPPT-трекерів.</li>
  <li>Діапазон робочих напруг.</li>
  <li>Наявність моніторингу через застосунок.</li>
</ol>
<p>Правильно підібраний інвертор зменшує втрати й спрощує сервіс.</p>
""",
    },
    {
        "slug": "kriplennya-na-dakh",
        "title": "Кріплення на дах: метал, черепиця, бітум",
        "excerpt": "Типи кріплень і типові помилки монтажу, які дорого виправляти пізніше.",
        "scene": "mounting",
        "body": """
<p>Якісне кріплення — це безпека конструкції на 25+ років. Економія на профілі та гідроізоляції майже завжди обертається протіканнями.</p>
<ul>
  <li>металочерепиця — гачки / рейки з ущільнювачами;</li>
  <li>фальц — кляммери без свердління;</li>
  <li>бітум / мембрана — спеціальні опори з герметизацією.</li>
</ul>
<p>Перед монтажем перевіряємо несучу здатність покрівлі та снігове навантаження регіону.</p>
""",
    },
    {
        "slug": "chy-potriben-akumulyator",
        "title": "Чи потрібен акумулятор для домашньої станції",
        "excerpt": "Коли батарея справді окупається, а коли краще стартувати з мережевої СЕС.",
        "scene": "battery",
        "body": """
<p>Акумулятор підвищує автономність, але збільшує бюджет. Рішення залежить від мети:</p>
<ul>
  <li>резерв на відключення — так, гібрид + АКБ;</li>
  <li>максимальна економія на тарифі — спочатку мережева СЕС;</li>
  <li>повна автономія — окремий проєкт із розрахунком навантаження.</li>
</ul>
<p>У більшості кейсів вигідно спочатку запустити генерацію, а накопичувач додати другим етапом.</p>
""",
    },
    {
        "slug": "yak-rakhuvaty-okupnist",
        "title": "Як рахувати окупність сонячної станції",
        "excerpt": "Формула без магії: споживання, тариф, власне споживання та сервісні витрати.",
        "scene": "payback",
        "body": """
<p>Окупність — це не рекламний слоган, а простий розрахунок грошового потоку.</p>
<ol>
  <li>Річне виробництво станції, кВт·год.</li>
  <li>Частка власного споживання.</li>
  <li>Вартість кВт·год за вашим тарифом.</li>
  <li>Витрати на обслуговування.</li>
</ol>
<blockquote><p>Чим вища частка самоспоживання, тим швидша окупність.</p></blockquote>
<p>Soliron допомагає зробити попередній розрахунок під ваш рахунок за електроенергію.</p>
""",
    },
    {
        "slug": "obslugovuvannya-ses",
        "title": "Обслуговування СЕС протягом року",
        "excerpt": "Що перевіряти щосезону, щоб станція працювала стабільно й безпечно.",
        "scene": "maintenance",
        "body": """
<p>Сучасні станції майже не потребують щоденного догляду, але сезонний огляд обовʼязковий.</p>
<ul>
  <li>очищення модулів від пилу та листя;</li>
  <li>перевірка кріплень після зими;</li>
  <li>контроль помилок інвертора;</li>
  <li>огляд кабелів і зʼєднань.</li>
</ul>
<p>Регулярний сервіс продовжує ресурс обладнання й зберігає гарантію.</p>
""",
    },
    {
        "slug": "mify-pro-sonyachnu-energetyku",
        "title": "Міфи про сонячну енергетику",
        "excerpt": "Розбираємо популярні твердження: «не працює взимку», «панелі небезпечні», «окупається 30 років».",
        "scene": "myths",
        "body": """
<p>Навколо СЕС багато міфів. Ось факти:</p>
<ul>
  <li>взимку станція працює, хоча виробіток нижчий;</li>
  <li>якісні панелі сертифіковані й безпечні при правильному монтажі;</li>
  <li>для домогосподарств окупність часто вимірюється роками, а не десятиліттями.</li>
</ul>
<p>Головне — коректний проєкт і комплектація під реальне споживання.</p>
""",
    },
    {
        "slug": "pidklyuchennya-do-merezhi",
        "title": "Підключення до мережі: що підготувати",
        "excerpt": "Документи, технічні умови та послідовність кроків для введення станції в роботу.",
        "scene": "grid",
        "body": """
<p>Навіть готова комплектація не запуститься без коректного підключення.</p>
<ol>
  <li>Технічні умови / дозвільні документи.</li>
  <li>Схема підключення та захист.</li>
  <li>Пусконалагодження інвертора.</li>
  <li>Перевірка обліку та моніторингу.</li>
</ol>
<p>Команда Soliron супроводжує клієнта на ключових етапах запуску.</p>
""",
    },
    {
        "slug": "ses-dlya-biznesu",
        "title": "СЕС для бізнесу: з чого почати",
        "excerpt": "Комерційна станція відрізняється масштабом, графіком навантаження і вимогами до обліку.",
        "scene": "business",
        "body": """
<p>Для підприємства сонячна станція — інструмент зниження собівартості енергії в години роботи виробництва.</p>
<ul>
  <li>аналіз профілю споживання;</li>
  <li>розрахунок пікових навантажень;</li>
  <li>вибір місця розміщення (дах / земля / навіс);</li>
  <li>план етапного розширення.</li>
</ul>
<p>Починайте з енергоаудиту — він окупає себе ще до закупівлі обладнання.</p>
""",
    },
    {
        "slug": "yak-chytaty-pasport-paneli",
        "title": "Як читати паспорт сонячної панелі",
        "excerpt": "Pmax, Voc, Isc, NOCT — коротко про параметри, які варто перевірити перед покупкою.",
        "scene": "passport",
        "body": """
<p>У паспорті модуля багато абревіатур. Найважливіші:</p>
<ul>
  <li><strong>Pmax</strong> — номінальна потужність;</li>
  <li><strong>Voc / Isc</strong> — напруга / струм короткого замикання;</li>
  <li><strong>NOCT</strong> — поведінка при реальній температурі;</li>
  <li>гарантія на потужність і продукт.</li>
</ul>
<p>Порівнюйте модулі не лише за ватою, а й за деградацією та умовами гарантії.</p>
""",
    },
    {
        "slug": "cheklist-pered-zapuskom",
        "title": "Чекліст перед запуском станції",
        "excerpt": "Фінальна перевірка перед першим увімкненням: механіка, електрика, моніторинг.",
        "scene": "checklist",
        "body": """
<p>Перед пуском пройдіться чеклістом разом із монтажною бригадою:</p>
<ol>
  <li>усі модулі закріплені, кабелі захищені;</li>
  <li>заземлення та УЗО/автомати встановлені;</li>
  <li>інвертор оновлений і налаштований;</li>
  <li>моніторинг показує коректні дані;</li>
  <li>користувач отримав інструкцію з експлуатації.</li>
</ol>
<p>Після запуску збережіть документи, серійні номери та доступи до кабінету моніторингу.</p>
""",
    },
]


def _slug_for(item: dict) -> str:
    return f"{DEMO_SLUG_PREFIX}{item['slug']}"[:160]


def _body_with_inline_image(body: str, image_url: str) -> str:
    figure = f'<figure><img src="{image_url}" alt="Ілюстрація до статті"></figure>'
    if "</h2>" in body:
        return body.replace("</h2>", f"</h2>\n{figure}", 1)
    if "</p>" in body:
        return body.replace("</p>", f"</p>\n{figure}", 1)
    return body + figure


def _apply_cover(post: BlogPost, scene: str, filename: str, body_html: str) -> None:
    cover = make_cover(scene, filename)
    post.cover_image.save(Path(cover.name).name, cover, save=False)
    post.body = _body_with_inline_image(body_html, post.cover_image.url)
    post.save()


class Command(BaseCommand):
    help = "Створює 12 демо-статей блогу з тематичними обкладинками та HTML-форматуванням"

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Видалити попередні demo-* статті перед створенням",
        )

    def handle(self, *args, **options):
        if options["reset"]:
            deleted, _ = BlogPost.objects.filter(slug__startswith=DEMO_SLUG_PREFIX).delete()
            self.stdout.write(f"Видалено demo-статей: {deleted}")

        now = timezone.now()
        created = 0
        updated = 0

        for index, item in enumerate(ARTICLES):
            slug = _slug_for(item)
            published_at = now - timedelta(days=index * 3 + 1)
            body_html = item["body"].strip()

            post, was_created = BlogPost.objects.update_or_create(
                slug=slug,
                defaults={
                    "title": item["title"],
                    "excerpt": item["excerpt"],
                    "body": body_html,
                    "is_published": True,
                    "published_at": published_at,
                },
            )
            _apply_cover(post, item["scene"], f"{slug}.jpg", body_html)

            created += int(was_created)
            updated += int(not was_created)
            self.stdout.write(f"{'+' if was_created else '~'} {post.slug}")

        hello = BlogPost.objects.filter(slug="hello").first()
        if hello is not None:
            if not hello.excerpt:
                hello.excerpt = "Коротко про старт блогу Soliron та сонячні рішення для дому."
            hello.is_published = True
            if hello.published_at is None:
                hello.published_at = now - timedelta(days=2)
            hello.save()
            _apply_cover(hello, "default", "hello-cover.jpg", hello.body or "<p>Перша стаття блогу Soliron.</p>")
            self.stdout.write(f"~ {hello.slug} (обкладинка)")

        total_published = BlogPost.objects.filter(is_published=True).count()
        self.stdout.write(
            self.style.SUCCESS(
                f"Готово: створено {created}, оновлено {updated}. "
                f"Опубліковано всього: {total_published}"
            )
        )
