#!/usr/bin/env python3
"""Генерація solironsitemap.pdf за Технічне_завдання_Голінковський.docx."""

from datetime import date
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

OUTPUT = Path(__file__).parent / "solironsitemap.pdf"
VERSION = "1.1"
TZ_SOURCE = "Технічне_завдання_Голінковський.docx"

FONT_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/Library/Fonts/Arial Unicode.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]

INK = colors.HexColor("#1A1A1A")
MUTED = colors.HexColor("#5A5550")
ACCENT = colors.HexColor("#1F3A5F")
ACCENT_2 = colors.HexColor("#2C5282")
HEADER_BG = colors.HexColor("#E8EEF5")
GRID = colors.HexColor("#C5CED9")
ROW_ALT = colors.HexColor("#F7F9FC")


def register_font() -> str:
    for path in FONT_CANDIDATES:
        if Path(path).exists():
            pdfmetrics.registerFont(TTFont("SiteFont", path))
            return "SiteFont"
    raise FileNotFoundError("Не знайдено шрифт із підтримкою кирилиці")


def p(text: str, style) -> Paragraph:
    return Paragraph(text.replace("\n", "<br/>"), style)


def build_styles(base_font: str):
    getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "title",
            fontName=base_font,
            fontSize=20,
            leading=26,
            alignment=TA_CENTER,
            spaceAfter=4,
            textColor=ACCENT,
        ),
        "subtitle": ParagraphStyle(
            "subtitle",
            fontName=base_font,
            fontSize=10,
            leading=13,
            alignment=TA_CENTER,
            spaceAfter=12,
            textColor=MUTED,
        ),
        "h1": ParagraphStyle(
            "h1",
            fontName=base_font,
            fontSize=13,
            leading=17,
            spaceBefore=12,
            spaceAfter=6,
            textColor=ACCENT,
        ),
        "h2": ParagraphStyle(
            "h2",
            fontName=base_font,
            fontSize=11,
            leading=14,
            spaceBefore=8,
            spaceAfter=4,
            textColor=ACCENT_2,
        ),
        "body": ParagraphStyle(
            "body",
            fontName=base_font,
            fontSize=9,
            leading=12,
            spaceAfter=4,
            alignment=TA_LEFT,
            textColor=INK,
        ),
        "footer": ParagraphStyle(
            "footer",
            fontName=base_font,
            fontSize=8,
            leading=10,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#888888"),
        ),
        "cell": ParagraphStyle(
            "cell",
            fontName=base_font,
            fontSize=8,
            leading=11,
            alignment=TA_LEFT,
            textColor=INK,
            wordWrap="CJK",
        ),
        "cell_header": ParagraphStyle(
            "cell_header",
            fontName=base_font,
            fontSize=8,
            leading=11,
            alignment=TA_LEFT,
            textColor=ACCENT,
            wordWrap="CJK",
        ),
    }


def _cell(text, style, header: bool = False) -> Paragraph:
    safe = (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
    if header:
        safe = f"<b>{safe}</b>"
    return Paragraph(safe, style)


def tree_table(rows, col_widths, styles):
    wrapped = []
    for row_idx, row in enumerate(rows):
        wrapped_row = []
        for cell in row:
            style = styles["cell_header"] if row_idx == 0 else styles["cell"]
            if isinstance(cell, Paragraph):
                wrapped_row.append(cell)
            else:
                wrapped_row.append(_cell(cell, style, header=row_idx == 0))
        wrapped.append(wrapped_row)

    table = Table(wrapped, colWidths=col_widths, hAlign="LEFT", repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
                ("GRID", (0, 0), (-1, -1), 0.25, GRID),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, ROW_ALT]),
            ]
        )
    )
    return table


def add_header_footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("SiteFont", 8)
    canvas.setFillColor(MUTED)
    canvas.drawString(
        1.6 * cm,
        A4[1] - 1.1 * cm,
        "Soliron · solironsitemap.pdf · на основі ТЗ · PrometeyLabs format",
    )
    canvas.drawRightString(A4[0] - 1.6 * cm, A4[1] - 1.1 * cm, f"v{VERSION}")
    canvas.drawCentredString(A4[0] / 2, 1.0 * cm, str(doc.page))
    canvas.restoreState()


def main():
    font = register_font()
    s = build_styles(font)
    today = date.today().isoformat()

    doc = SimpleDocTemplate(
        str(OUTPUT),
        pagesize=A4,
        leftMargin=1.6 * cm,
        rightMargin=1.6 * cm,
        topMargin=1.8 * cm,
        bottomMargin=1.6 * cm,
        title="Soliron — карта сайту",
        author="PrometeyLabs",
    )

    story = []

    story.append(p("КАРТА САЙТУ / SITEMAP", s["title"]))
    story.append(
        p(
            "Корпоративний сайт з каталогом «Soliron» "
            "(сонячні панелі та системи кріплень)",
            s["subtitle"],
        )
    )
    story.append(
        p(
            "Документ фіксує публічну карту URL, структуру адмін-панелі, інтеграції "
            "та критерії «ГОТОВО» за ТЗ. Формат узгоджений із базою знань Prometey "
            "(seo_skill · ecommerce_business_logic_skill · 500b2 · референс "
            "notenhausSitemap / sitemapcommerce / DidenkoSitemap).",
            s["body"],
        )
    )
    story.append(
        p(
            f"Версія: {today} · v{VERSION} · Джерело: {TZ_SOURCE}<br/>"
            "Рішення: лише UA · без сторінок поза ТЗ §3 · категорії — шаблон URL "
            "(дерево пізніше) · checkout один URL / 3 кроки HTMX · сповіщення лише Email · "
            "без домену в документі",
            s["body"],
        )
    )
    story.append(HRFlowable(width="100%", thickness=1, color=ACCENT))
    story.append(Spacer(1, 6))

    # 1. Метадані
    story.append(p("1. Метадані та статус рішень", s["h1"]))
    meta = [
        ["Параметр", "Статус / рішення"],
        [
            "Назва проєкту",
            "Soliron — корпоративний сайт з каталогом (панелі / кріплення)",
        ],
        ["Мова", "UA (єдина; без /uk/ і без мовних дзеркал)"],
        ["URL-підхід", "ЧПУ UA-трансліт; lowercase + дефіси (seo_skill)"],
        ["Стек", "HTML/CSS/JS + HTMX · Python/Django (ТЗ §2.1)"],
        ["Адаптив", "320px → 1920px; sticky header (ТЗ §2.2, §3)"],
        ["Браузери", "Chrome, Safari, Firefox, Edge — останні версії (ТЗ §2.3)"],
        ["PageSpeed", "≥75 mobile / ≥90 desktop (ТЗ §2.4)"],
        ["SEO-база", "sitemap.xml · robots.txt · ЧПУ (ТЗ §2.5)"],
        [
            "Оплата",
            "Онлайн-оплата відсутня; інфо: рахунок-фактура або готівка (ТЗ §3, §4.2)",
        ],
        ["Доставка", "Самовивіз · Delivery · Нова Пошта API (місто + відділення)"],
        ["Сповіщення", "Лише Email адміністратора (без Telegram у MVP)"],
        ["Домен", "Не зафіксовано — у документі лише бренд Soliron"],
        [
            "Категорії",
            "Дерево відсутнє на дату карти; у URL — шаблон /katalog/{slug}/…",
        ],
        [
            "Критерій «ГОТОВО»",
            "Повний UX-сценарій без Fatal/404/500 + відповідність ТЗ + адаптив (ТЗ §1)",
        ],
    ]
    story.append(tree_table(meta, [4.2 * cm, 13.2 * cm], s))

    # 2. Публічний сайт
    story.append(p("2. Публічний сайт — карта URL", s["h1"]))
    story.append(
        p(
            "Кожен рядок нижче — обовʼязковий для sitemap-coverage verify "
            "(ecommerce_business_logic_skill). Службові маршрути — поза меню. "
            "Сторінки поза ТЗ §3 у MVP не додаються.",
            s["body"],
        )
    )
    public = [
        ["Розділ", "URL", "Примітка / критерій «ГОТОВО»"],
        [
            "Головна",
            "/",
            "Шапка (лого, контакти, sticky), головний банер, блоки категорій, "
            "переваги, footer; усі лінки клікабельні (ТЗ §3)",
        ],
        [
            "Каталог",
            "/katalog/",
            "Сітка товарів, breadcrumbs, фільтр за категоріями; empty → "
            "«Нічого не знайдено» (ТЗ §3, §6.1)",
        ],
        [
            "Категорія / підкатегорія",
            "/katalog/{slug}/…",
            "Ієрархія slug; конкретне дерево — контент CMS пізніше, не жорстко в карті",
        ],
        [
            "Товар (PDP)",
            "/tovar/{slug}/",
            "Галерея, назва, опис, ціна/статус, «Купити» → кошик без reload; "
            "лічильник у шапці (ТЗ §3)",
        ],
        [
            "Пошук",
            "/poshuk/?q=",
            "Пошук за ТЗ §6.1 (навігація + пошук); релевантні товари або "
            "«Нічого не знайдено»",
        ],
        [
            "Кошик",
            "/koshyk/",
            "Перелік, зміна кількості, перехід до оформлення (ТЗ §3)",
        ],
        [
            "Оформлення (Checkout)",
            "/oformlennya/",
            "Один URL · 3 кроки HTMX (контакти → доставка → підтвердження); "
            "блок «Ваше замовлення» на кожному кроці (ТЗ §3)",
        ],
        [
            "Екран подяки",
            "/oformlennya/ (стан після submit)",
            "Після «Підтвердити замовлення»: запис у БД + Email адміну + "
            "екран подяки (ТЗ §3) — окремий публічний розділ не вводиться",
        ],
        [
            "Блог (список)",
            "/blog/",
            "Статті з пагінацією або «Показати ще» (ТЗ §3)",
        ],
        [
            "Стаття блогу",
            "/blog/{slug}/",
            "Текст зі збереженням форматування, зображення, дата (ТЗ §3, §6.5)",
        ],
        [
            "Контакти",
            "/kontakty/",
            "Телефони, email, адреса, інтерактивна карта, форма ЗЗ AJAX (ТЗ §3, §6.3/§6.6)",
        ],
        ["XML sitemap", "/sitemap.xml", "Автогенерація публічних URL (ТЗ §2.5)"],
        [
            "robots",
            "/robots.txt",
            "Disallow: /admin/; Sitemap: … (seo_skill)",
        ],
        ["Помилки", "404 / 500", "Шаблони помилок (системні)"],
    ]
    story.append(tree_table(public, [3.4 * cm, 4.6 * cm, 9.4 * cm], s))

    story.append(p("2.1. Глобальна шапка / підвал", s["h2"]))
    story.append(
        p(
            "<b>Header (sticky):</b> логотип → / · Каталог · Блог · Контакти · "
            "пошук · іконка кошика з лічильником · контакти в шапці (ТЗ §3).<br/>"
            "<b>Footer:</b> навігація (Каталог, Блог, Контакти) · контакти · копірайт Soliron.",
            s["body"],
        )
    )

    story.append(p("2.2. Головна — блоки (ТЗ §3)", s["h2"]))
    home = [
        ["Блок", "Зміст", "ГОТОВО"],
        ["Шапка", "Лого, контакти, меню, кошик", "Фіксується при скролі"],
        ["Hero / банер", "Головний банер", "Коректне відображення 320–1920"],
        ["Категорії", "Блоки категорій → /katalog/{slug}/", "Кліки ведуть у каталог"],
        ["Переваги", "Переваги компанії", "Читабельно на mobile / iOS Safari"],
        ["Підвал", "Навігація + контакти", "Усі посилання клікабельні"],
    ]
    story.append(tree_table(home, [3.2 * cm, 7.5 * cm, 6.7 * cm], s))

    story.append(p("2.3. Картка товару (PDP) — /tovar/{slug}/", s["h2"]))
    pdp = [
        ["Елемент", "Вимога / ГОТОВО"],
        ["Галерея", "Фото гортаються без збоїв"],
        ["Контент", "Назва, детальний опис, ціна або статус наявності"],
        [
            "«Купити»",
            "Додає 1+ товарів у кошик без перезавантаження (HTMX); лічильник у шапці оновлюється",
        ],
        ["Онлайн-оплата", "Відсутня (ТЗ §3, §4.2)"],
    ]
    story.append(tree_table(pdp, [4.0 * cm, 13.4 * cm], s))

    story.append(p("2.4. Checkout — один URL /oformlennya/ · 3 кроки (ТЗ §3)", s["h2"]))
    checkout = [
        ["Крок", "Поля / дія", "ГОТОВО"],
        [
            "1. Контакти",
            "ПІБ* · Телефон* · Email · Компанія",
            "Валідація обовʼязкових; блок помилок зрозумілий",
        ],
        [
            "2. Доставка",
            "Самовивіз / Delivery / Нова Пошта + місто/відділення (API) · Коментар",
            "Пошук НП без зависань; відділення у замовленні",
        ],
        [
            "3. Підтвердження",
            "Підсумок даних · інфо про оплату (рахунок / готівка) · «Підтвердити»",
            "Запис у БД + Email адміну + екран подяки",
        ],
        [
            "Сайдбар",
            "«Ваше замовлення»: товари, qty, сума — на кожному кроці",
            "Зміна qty у кошику працює",
        ],
    ]
    story.append(tree_table(checkout, [3.4 * cm, 8.0 * cm, 6.0 * cm], s))

    story.append(PageBreak())

    # 3. Адмінка
    story.append(p("3. Адмін-панель — карта модулів (ТЗ §5)", s["h1"]))
    story.append(
        p(
            "Сайдбар дзеркалить структуру сайту, а не Django apps (zettel 500b2 / admin_skill). "
            "Зміни каталогу на вітрині ≤ 1 хвилини з урахуванням кешу (ТЗ §5.1).",
            s["body"],
        )
    )
    admin = [
        ["Модуль", "Зона", "Функції · критерій «ГОТОВО»"],
        [
            "Дашборд",
            "/admin/",
            "Огляд нових замовлень/заявок, швидкі посилання",
        ],
        [
            "Категорії",
            "каталог",
            "CRUD категорій і підкатегорій (дерево заповнюється пізніше)",
        ],
        [
            "Товари",
            "каталог",
            "CRUD товарів: фото, ціна, статус наявності, slug; зміни ≤1 хв на вітрині",
        ],
        [
            "Замовлення / ліди",
            "ліди",
            "Список + деталі: товари, клієнт, доставка/відділення, коментар, дата (ТЗ §5.2)",
        ],
        [
            "Блоки головної",
            "контент",
            "Банери, переваги, текстові блоки (ТЗ §5.3)",
        ],
        [
            "Контакти сайту",
            "контент",
            "Телефони, email, адреса, координати карти (ТЗ §5.3)",
        ],
        [
            "Блог",
            "блог",
            "CRUD статей: WYSIWYG, головне зображення, публікація (ТЗ §5.4)",
        ],
        [
            "Форми ЗЗ",
            "ліди",
            "Заявки з /kontakty/ у БД + доступ менеджеру",
        ],
        [
            "Налаштування",
            "налаштування",
            "Email адміна, ключі НП/GTM/GA4 — лише через env, не в git",
        ],
    ]
    story.append(tree_table(admin, [3.6 * cm, 2.8 * cm, 11.0 * cm], s))

    # 4. Інтеграції
    story.append(p("4. Інтеграції та форми (ТЗ §4)", s["h1"]))
    integ = [
        ["Сервіс", "Точки / маршрути", "Критерій «ГОТОВО»"],
        [
            "Email адміна",
            "бекенд notify",
            "Замовлення + форма ЗЗ: повні дані (товари, сума, контакти, "
            "доставка/відділення, коментар) миттєво на Email (ТЗ §4.1)",
        ],
        [
            "Нова Пошта API",
            "у /oformlennya/ крок 2",
            "Пошук міста + вибір відділення; без розрахунку вартості доставки (ТЗ §4.2)",
        ],
        [
            "Онлайн-оплата",
            "—",
            "Відсутня; інфо про рахунок-фактуру / готівку на кроці 3",
        ],
        [
            "Форма ЗЗ",
            "POST AJAX /kontakty/",
            "Без reload; повідомлення подяки; запис у CMS + Email (ТЗ §6.3, §6.6)",
        ],
        [
            "GA4 + GTM",
            "контейнер у base",
            "Події: add_to_cart, purchase/order_success, form_submit, клік контактів (ТЗ §7.1)",
        ],
    ]
    story.append(tree_table(integ, [3.4 * cm, 4.8 * cm, 9.2 * cm], s))
    story.append(
        p(
            "<b>Умова ТЗ §4.3:</b> додаткові зовнішні сервіси — лише після надання "
            "Замовником доступів, API-ключів і акаунтів. Telegram у MVP не входить "
            "(узгоджено: лише Email).",
            s["body"],
        )
    )

    # 5. E2E
    story.append(p("5. E2E чек-лист ↔ URL (ТЗ §6)", s["h1"]))
    e2e = [
        ["№", "Тест-кейс", "URL / покриття"],
        [
            "1",
            "Навігація по категоріях + пошук; empty-state",
            "/katalog/ · /katalog/{slug}/ · /poshuk/?q=",
        ],
        [
            "2",
            "Повний цикл: каталог → фільтр → PDP → кілька «Купити» → "
            "кошик → 3 кроки (вкл. НП) → підтвердження",
            "/katalog/ → /tovar/{slug}/ → /koshyk/ → /oformlennya/",
        ],
        [
            "3",
            "Форма ЗЗ AJAX + подяка + Email адміну",
            "/kontakty/",
        ],
        [
            "4",
            "Некоректні дані — блок + підказки",
            "/oformlennya/ · /kontakty/",
        ],
        [
            "5",
            "Блог → відкриття статті",
            "/blog/ → /blog/{slug}/",
        ],
        [
            "6",
            "Форма на Контактах (повторний сценарій приймання)",
            "/kontakty/",
        ],
    ]
    story.append(tree_table(e2e, [1.0 * cm, 8.2 * cm, 8.2 * cm], s))

    story.append(PageBreak())

    # 6. Roadmap
    story.append(p("6. Модульний roadmap (ядро за ТЗ)", s["h1"]))
    road = [
        ["Фаза", "Склад", "Статус"],
        [
            "M0 Вітрина",
            "Sticky header/footer, головна, /katalog/+/ {slug}/, /tovar/{slug}/, "
            "/poshuk/, /blog/+/ {slug}/, /kontakty/",
            "Обовʼязково",
        ],
        [
            "M1 Комерція",
            "Кошик, /oformlennya/ (3 кроки), валідація, екран подяки, замовлення в БД, Email",
            "Обовʼязково",
        ],
        [
            "M2 Доставка",
            "Нова Пошта API (місто + відділення) без розрахунку вартості",
            "Обовʼязково",
        ],
        [
            "M3 Адмінка",
            "CRUD категорій/товарів, замовлення/ліди, блоки, контакти, блог WYSIWYG, SLA ≤1 хв",
            "Обовʼязково",
        ],
        [
            "M4 SEO/Perf",
            "sitemap.xml, robots, ЧПУ, PageSpeed ≥75/90",
            "Обовʼязково",
        ],
        [
            "M5 Аналітика",
            "GTM + GA4 + події (кошик, замовлення, форми, кліки контактів)",
            "Обовʼязково (ТЗ §7.1)",
        ],
        [
            "Backlog",
            "Дерево категорій (контент), домен, сторінки поза ТЗ, Telegram, "
            "онлайн-оплата, Google Ads кампанія",
            "Поза MVP",
        ],
    ]
    story.append(tree_table(road, [2.6 * cm, 11.2 * cm, 3.6 * cm], s))

    # 7. Coverage
    story.append(p("7. Sitemap-coverage verify (шаблон здачі)", s["h1"]))
    story.append(
        p(
            "Заповнюється на етапі реалізації. Будь-який рядок без статусу — "
            "блокер приймання (ERR-BIZ-01).",
            s["body"],
        )
    )
    cov = [
        ["URL з карти", "urls", "View", "Шаблон", "Навігація", "Статус"],
        ["/", "☐", "☐", "☐", "☐", ""],
        ["/katalog/", "☐", "☐", "☐", "☐", ""],
        ["/katalog/{slug}/…", "☐", "☐", "☐", "☐", ""],
        ["/tovar/{slug}/", "☐", "☐", "☐", "☐", ""],
        ["/poshuk/?q=", "☐", "☐", "☐", "☐", ""],
        ["/koshyk/", "☐", "☐", "☐", "☐", ""],
        ["/oformlennya/", "☐", "☐", "☐", "☐", ""],
        ["/blog/", "☐", "☐", "☐", "☐", ""],
        ["/blog/{slug}/", "☐", "☐", "☐", "☐", ""],
        ["/kontakty/", "☐", "☐", "☐", "☐", ""],
        ["/sitemap.xml", "☐", "☐", "—", "—", ""],
        ["/robots.txt", "☐", "☐", "—", "—", ""],
    ]
    story.append(
        tree_table(
            cov,
            [5.0 * cm, 1.8 * cm, 1.8 * cm, 2.2 * cm, 2.6 * cm, 4.0 * cm],
            s,
        )
    )

    story.append(Spacer(1, 10))
    story.append(
        p(
            f"Референс формату: notenhausSitemap.pdf · sitemapcommerce.pdf · "
            f"DidenkoSitemap.pdf<br/>Документ: solironsitemap.pdf · "
            f"Версія: {today} v{VERSION} · Джерело: {TZ_SOURCE}",
            s["footer"],
        )
    )

    doc.build(story, onFirstPage=add_header_footer, onLaterPages=add_header_footer)
    print(f"OK → {OUTPUT}")


if __name__ == "__main__":
    main()
