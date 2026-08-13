"""UNFOLD sidebar: структура сайту + службові розділи (500b2 / admin_skill)."""

from django.urls import reverse_lazy


def build_navigation(request=None):
    return [
        {
            "title": "Сторінки сайту",
            "separator": False,
            "items": [
                {
                    "title": "Головна",
                    "icon": "home",
                    "link": reverse_lazy("admin:content_homepage_changelist"),
                },
                {
                    "title": "Переваги (блок на головній)",
                    "icon": "verified",
                    "link": reverse_lazy("admin:content_homeadvantage_changelist"),
                },
                {
                    "title": "Блог",
                    "icon": "article",
                    "link": reverse_lazy("admin:content_blogpost_changelist"),
                },
                {
                    "title": "Налаштування / контакти",
                    "icon": "settings",
                    "link": reverse_lazy("admin:content_sitesettings_changelist"),
                },
            ],
        },
        {
            "title": "Каталог",
            "separator": True,
            "items": [
                {
                    "title": "Категорії",
                    "icon": "category",
                    "link": reverse_lazy("admin:catalog_category_changelist"),
                },
                {
                    "title": "Товари",
                    "icon": "inventory_2",
                    "link": reverse_lazy("admin:catalog_product_changelist"),
                },
            ],
        },
        {
            "title": "Комерція",
            "separator": True,
            "items": [
                {
                    "title": "Замовлення",
                    "icon": "shopping_bag",
                    "link": reverse_lazy("admin:commerce_order_changelist"),
                },
                {
                    "title": "Кошики",
                    "icon": "shopping_cart",
                    "link": reverse_lazy("admin:commerce_cart_changelist"),
                },
                {
                    "title": "Заявки ЗЗ",
                    "icon": "inbox",
                    "link": reverse_lazy("admin:content_contactlead_changelist"),
                },
            ],
        },
        {
            "title": "Доставка НП",
            "separator": True,
            "items": [
                {
                    "title": "НП міста",
                    "icon": "location_city",
                    "link": reverse_lazy("admin:shipping_npcity_changelist"),
                },
                {
                    "title": "НП відділення",
                    "icon": "local_shipping",
                    "link": reverse_lazy("admin:shipping_npwarehouse_changelist"),
                },
            ],
        },
        {
            "title": "Система",
            "separator": True,
            "items": [
                {
                    "title": "Редиректи 301",
                    "icon": "alt_route",
                    "link": reverse_lazy("admin:seo_redirect301_changelist"),
                },
                {
                    "title": "Email логи",
                    "icon": "mail",
                    "link": reverse_lazy("admin:notifications_emaillog_changelist"),
                },
                {
                    "title": "Користувачі",
                    "icon": "person",
                    "link": reverse_lazy("admin:auth_user_changelist"),
                },
                {
                    "title": "Групи",
                    "icon": "group",
                    "link": reverse_lazy("admin:auth_group_changelist"),
                },
                {
                    "title": "Банери (legacy)",
                    "icon": "image",
                    "link": reverse_lazy("admin:content_homebanner_changelist"),
                },
            ],
        },
    ]
