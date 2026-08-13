# Soliron — схема БД (tables.md)

**Версія:** 1.2 · **Дата:** 2026-08-04 · **Статус lock:** APPROVED + scaffold  
**Джерела:** `Технічне_завдання_Голінковський.docx` · `solironsitemap.pdf` v1.1  
**Регламент:** Prometey `ecommerce_db_schema_skill` + `ecommerce-db-schema-reference` + `novaposhta_skill`  
**Стек:** Django 5+ · PostgreSQL · пакет `src.*` · UA only · HTMX · Email (без Telegram) · без онлайн-оплати

---

## 0. Scratchpad / lock (затверджено)

| Тема | Рішення |
|---|---|
| Apps пакет | `src.*` |
| Shipping | окремий app `shipping` |
| Auth | лише staff Django `auth.User` (без кастомного `AUTH_USER_MODEL`, без кабінету) |
| Мова | UA only; ЧПУ UA-трансліт |
| Ціна | `price_uah` (nullable) **або** текстовий статус наявності/ціни (ТЗ §3) |
| «Купити» без ціни / `call` | **дозволено**; `unit_price_uah` може бути NULL |
| Товар↔категорія | лише `product.category_id` (без M2M) |
| Категорії | дерево `parent_id`; конкретне L1/L2 — контент пізніше |
| Checkout | один URL `/oformlennya/` · 3 кроки HTMX |
| Доставка | `pickup` \| `delivery` \| `nova_poshta`; **без** вартості й **без** ТТН |
| НП довідник | за `novaposhta_skill`: таблиці кешу + sync; пошук на checkout **лише з локальної БД** |
| Delivery Auto | кеш міст/складів + sync (`sync_delivery_data`); checkout: склад \| двері; snapshot на order; **без** calc/ТТН (ТЗ) |
| Оплата | онлайн відсутня; на кроці 3 інфо «рахунок-фактура / готівка» → `payment_method` snapshot |
| Сповіщення | лише Email адміну (замовлення + ЗЗ) |
| Форма ЗЗ | `name*` · `phone*` · `message*` · `email` опційно (затверджено) |
| Сторінки поза ТЗ | не створюємо (`/pro-nas/`, політики тощо) |
| ~~`pricing`~~ | не створюємо |
| ~~`payments`~~ | не створюємо |
| ~~`accounts` / `cabinet`~~ | не створюємо |
| Roadmap ядра | M0–M4 (+ M5 аналітика = сніпети, не таблиці) |
| Backlog | дерево-контент, домен, Telegram, онлайн-оплата, Ads, ТТН |

### 0.1. Форма ЗЗ — обовʼязкові поля (затверджено 2026-07-30)

`name*` · `phone*` · `message*` · `email` опційно.  
Валідація в `create_contact_lead` + на формі (ТЗ §6.3 / §6.4).

`core` — shared kernel mixins лише (`TimeStampedModel`, `SeoFieldsMixin`), **без** бізнес-таблиць.

---

## 1. Apps

| App | Відповідальність | Таблиці |
|---|---|---|
| `core` | mixins, context processors | — |
| `catalog` | категорії, товари, галерея, пошук | `category`, `product`, `product_image` |
| `commerce` | кошик, замовлення, checkout | `cart`, `cart_item`, `order`, `order_item` |
| `shipping` | НП + Delivery sync + autocomplete з БД; snapshot на order | `np_*`, `delivery_*` (обовʼязково) |
| `content` | головна, контакти, блог, ЗЗ, site_settings | `site_settings`, `home_page`, `home_banner` (legacy), `home_advantage`, `blog_post`, `contact_lead` |
| `notifications` | Email адміну | `email_log` |
| `seo` | sitemap/robots views; 301 | `redirect_301` |

Адмін-сайдбар дзеркалить структуру сайту, не apps (`500b2`).

---

## 2. ER

```
catalog_category ──── 1:M ──── catalog_category   (parent_id, дерево)
catalog_category ──── 1:M ──── catalog_product    (product.category_id)
catalog_product  ──── 1:M ──── catalog_product_image

commerce_cart    ──── 1:M ──── commerce_cart_item ──→ catalog_product
commerce_order   ──── 1:M ──── commerce_order_item (snapshot назва/ціна/qty)
commerce_order   · shipping_method + np_* / delivery_* (snapshot)
commerce_order   · cart_id SET_NULL

shipping_np_city ──── 1:M ──── shipping_np_warehouse   (локальний довідник НП)
shipping_delivery_city ──── 1:M ──── shipping_delivery_warehouse  (локальний довідник Delivery)

content_site_settings   (singleton)
content_home_page       (singleton — тексти/фото головної)
content_home_banner     (legacy)
content_home_advantage
content_blog_post
content_contact_lead

notifications_email_log  (опційно)
seo_redirect_301         (опційно)
```

Кошик: `session_key`, без User. Покупець — guest snapshot на `order`. Staff бачить замовлення/ліди в адмінці.

---

## 3. Таблиці ядра

Типи: `PK` bigserial · гроші `numeric(12,2)` · slug `varchar(160)` · timestamps через mixin.

### 3.1. `catalog_category`

| Колонка | Тип | Null | Примітка |
|---|---|---|---|
| id | PK | | |
| parent_id | FK → category | ✓ | SET_NULL; корінь = NULL |
| name | varchar(255) | | |
| slug | varchar(160) | | unique **серед siblings** або global unique (обрати global unique для простішого URL) |
| description | text | ✓ | |
| image | varchar(512) | ✓ | ImageField; блок категорій на головній |
| card_badge_text | varchar(40) | ✓ | бейдж на картці (TOP / Новинка); порожньо = без бейджа |
| card_badge_style | varchar(16) | | `stock` \| `top` \| `sale` \| `soft` |
| is_active | bool | | default true |
| sort_order | int | | default 0 |
| seo_title / seo_description / seo_keywords | | ✓ | SeoFieldsMixin |
| created_at / updated_at | | | |

Індекси: `(parent_id, sort_order)`, `(is_active)`, unique `(slug)`.  
URL: `/katalog/{slug}/…` — резолв по slug (шлях через ancestors у коді / `path` materialized опційно пізніше).

**Рішення MVP:** `slug` **global unique** (простіший catch-all / резолв). Nested path у URL можна зібрати з ancestors без окремої колонки `path`.

### 3.2. `catalog_product`

| Колонка | Тип | Null | Примітка |
|---|---|---|---|
| id | PK | | |
| category_id | FK → category | ✓ | єдина категорія товару (без M2M); SET_NULL |
| name | varchar(255) | | |
| slug | varchar(160) | | unique → `/tovar/{slug}/` |
| description | text | ✓ | детальний опис (plain/HTML з TinyMCE) |
| price_uah | numeric(12,2) | ✓ | NULL = ціна не показується / «за запитом» |
| availability | varchar(32) | | `in_stock` \| `on_order` \| `out_of_stock` \| `call` |
| availability_label | varchar(120) | ✓ | кастомний текст статусу на PDP (якщо треба) |
| card_badge_text | varchar(40) | ✓ | бейдж на картці (TOP / -10%); порожньо = availability_label / availability |
| card_badge_style | varchar(16) | ✓ | `stock` \| `top` \| `sale` \| `soft` |
| sku | varchar(64) | ✓ | unique якщо заповнено; пошук |
| weight_kg | numeric(8,3) | | default 25; для майбутньої логістики Delivery |
| length_cm / width_cm / height_cm | int | | default 200 / 110 / 5; `volume_m3` = L×W×H/1e6 (property) |
| is_published | bool | | |
| sort_order | int | | default 0 |
| seo_title / seo_description / seo_keywords | | ✓ | |
| created_at / updated_at | | | |

Індекси: `(is_published, sort_order)`, `(category_id)`, `(availability)`, unique `(slug)`.  
Check: `price_uah IS NULL OR price_uah >= 0`.

**PDP «ціна або статус»:** якщо `price_uah` NOT NULL — показувати ціну; інакше / додатково — `availability_label` або label від `availability`.  
**«Купити»:** дозволено при `availability ∈ {in_stock, on_order, call}` і при `price_uah IS NULL`; заборонено лише `out_of_stock`.

Фільтр «за категоріями» = `category_id` товару ∈ піддереві обраної категорії (без M2M).

### 3.3. `catalog_product_image`

| Колонка | Тип | Null | Примітка |
|---|---|---|---|
| id | PK | | |
| product_id | FK cascade | | |
| image | varchar(512) | | ImageField |
| alt | varchar(255) | ✓ | |
| is_main | bool | | |
| sort_order | int | | |
| created_at | | | |

Partial unique: один `is_main=true` на product.

---

### 3.4. `commerce_cart`

| Колонка | Тип | Примітка |
|---|---|---|
| id | PK | |
| session_key | varchar(40) | indexed |
| status | varchar(20) | `active` \| `converted` \| `abandoned` |
| created_at / updated_at | | |

Partial index: `(session_key)` where `status='active'`.

### 3.5. `commerce_cart_item`

| Колонка | Тип | Примітка |
|---|---|---|
| id | PK | |
| cart_id | FK cascade | |
| product_id | FK restrict | |
| qty | int | ≥ 1 |
| unit_price_uah | numeric(12,2) | ✓ NULL якщо товар «без ціни» на момент add |
| Unique(cart_id, product_id) | | |

### 3.6. `commerce_order`

| Колонка | Тип | Null | Примітка |
|---|---|---|---|
| id | PK | | |
| number | varchar(32) | | unique (напр. `SL-YYYYMMDD-XXXX`) |
| status | varchar(20) | | `new` \| `processing` \| `completed` \| `cancelled` |
| customer_name | varchar(255) | | ПІБ * |
| customer_phone | varchar(32) | | * |
| customer_email | varchar(254) | ✓ | |
| customer_company | varchar(255) | ✓ | |
| customer_comment | text | ✓ | крок 2 |
| shipping_method | varchar(20) | | `pickup` \| `delivery` \| `nova_poshta` |
| delivery_mode | varchar(20) | ✓ | `warehouse` \| `doors` (лише для `delivery`) |
| delivery_city_id | varchar(64) | ✓ | snapshot Delivery city GUID |
| delivery_city_name | varchar(255) | ✓ | |
| delivery_warehouse_id | varchar(64) | ✓ | snapshot складу (режим `warehouse`) |
| delivery_warehouse_name | varchar(255) | ✓ | |
| delivery_address | text | ✓ | вулиця+будинок (режим `doors`) |
| delivery_cost_uah | numeric(12,2) | ✓ | резерв; у MVP ТЗ **не** заповнюємо (без calc) |
| tracking_number | varchar(64) | ✓ | резерв; ТТН — **backlog** |
| np_city_ref | varchar(64) | ✓ | snapshot НП |
| np_city_name | varchar(255) | ✓ | |
| np_warehouse_ref | varchar(64) | ✓ | |
| np_warehouse_name | varchar(255) | ✓ | |
| payment_method | varchar(20) | | `invoice` \| `cash` (інфо, не шлюз) |
| subtotal_uah | numeric(12,2) | | сума рядків (0 якщо всі без ціни) |
| total_uah | numeric(12,2) | | = subtotal (доставка не рахується) |
| cart_id | FK cart | ✓ | SET_NULL |
| email_sent_at | timestamptz | ✓ | лист адміну |
| created_at / updated_at | | | |

Індекси: `(status, created_at DESC)`, `(number)`, `(customer_phone)`, `(created_at DESC)`.

Check логіка в сервісі (не обовʼязково DB check):  
- `nova_poshta` → `np_city_*` + `np_warehouse_*` обовʼязкові  
- `delivery` + `warehouse` → `delivery_city_*` + `delivery_warehouse_*` обовʼязкові  
- `delivery` + `doors` → `delivery_city_*` + `delivery_address` обовʼязкові  
- `pickup` → NP/Delivery snapshot порожні

### 3.7. `commerce_order_item`

| Колонка | Тип | Null | Примітка |
|---|---|---|---|
| id | PK | | |
| order_id | FK cascade | | |
| product_id | FK | ✓ | SET_NULL |
| product_sku | varchar(64) | ✓ | snapshot |
| product_name | varchar(255) | | snapshot |
| qty | int | | ≥ 1 |
| unit_price_uah | numeric(12,2) | ✓ | snapshot; NULL якщо без ціни |
| line_total_uah | numeric(12,2) | ✓ | qty × unit або NULL |

---

### 3.8. `shipping_np_city` (обовʼязково · `novaposhta_skill`)

| Колонка | Тип | Примітка |
|---|---|---|
| id | PK | |
| ref | varchar(64) | unique (НП Ref) |
| name | varchar(255) | indexed; пошук icontains |
| area | varchar(255) | ✓ AreaDescription |
| is_active | bool | default true |
| updated_at | | |

Синк: management command / Celery — `Address.getCities`, `Page` **рядком**, `Limit: "500"`.

### 3.9. `shipping_np_warehouse` (обовʼязково · `novaposhta_skill`)

| Колонка | Тип | Примітка |
|---|---|---|
| id | PK | |
| ref | varchar(64) | unique |
| city_id | FK → np_city | CASCADE |
| number | varchar(16) | ✓ номер відділення |
| description | varchar(512) | назва/адреса |
| is_active | bool | default true |
| updated_at | | |

**Checkout:** `search_cities` / `list_warehouses` — **лише з локальної БД**, не live API (`novaposhta_skill` Фаза 1).  
ТТН / `np_sender` / `shipment` — **backlog**.

### 3.9b. `shipping_delivery_city` (Delivery Auto)

| Колонка | Тип | Примітка |
|---|---|---|
| id | PK | |
| city_id | varchar(64) | unique (GUID API) |
| name_uk | varchar(255) | indexed; пошук icontains |
| region_name | varchar(255) | ✓ |
| is_active | bool | default true |
| updated_at | | |

Синк: `manage.py sync_delivery_data` → `GetAreasList` (`fl_all=false` за замовчуванням).

### 3.9c. `shipping_delivery_warehouse` (Delivery Auto)

| Колонка | Тип | Примітка |
|---|---|---|
| id | PK | |
| warehouse_id | varchar(64) | unique (GUID API) |
| city_id | FK → delivery_city | CASCADE |
| name_uk | varchar(255) | |
| address_uk | varchar(512) | ✓ |
| phone | varchar(128) | ✓ |
| max_weight | numeric(10,2) | ✓ |
| warehouse_type | int | ✓ `0`/`3` = вантажний склад |
| is_freight | bool | default true; checkout лише freight |
| is_active | bool | default true |
| updated_at | | |

**Checkout:** `/api/delivery/cities/`, `/api/delivery/warehouses/` — **лише з локальної БД**.  
Вартість / ТТН Delivery — **не в MVP ТЗ** (backlog; HMAC-клієнт підготовлений).

---

### 3.10. `content_site_settings` (singleton)

| Колонка | Тип | Null | Примітка |
|---|---|---|---|
| id | PK | | лише 1 рядок |
| site_name | varchar(120) | | default `Soliron` |
| logo | varchar(512) | ✓ | |
| phone_primary | varchar(32) | ✓ | шапка |
| phone_secondary | varchar(32) | ✓ | |
| email | varchar(254) | ✓ | публічний |
| address | text | ✓ | |
| map_embed_url / map_lat / map_lng | | ✓ | інтерактивна карта на `/kontakty/` |
| notify_email | varchar(254) | | Email адміна для замовлень/ЗЗ |
| gtm_container_id | varchar(32) | ✓ | |
| ga4_measurement_id | varchar(32) | ✓ | |
| robots_txt | text | ✓ | редагування в адмінці |
| footer_tagline | text | ✓ | слоган футера |
| social_*_url / social_*_enabled | | ✓ | facebook, instagram, telegram, youtube |
| created_at / updated_at | | | |

### 3.10b. `content_home_page` (singleton)

Усі тексти/фото головної (hero, CTA, пропозиція, заголовки секцій). Картки переваг — `home_advantage`.

### 3.11. `content_home_banner` (legacy)

Не рендериться на фронті; контент головної — у `home_page`.

| Колонка | Тип | Null | Примітка |
|---|---|---|---|
| id | PK | | |
| title | varchar(255) | ✓ | |
| subtitle | text | ✓ | |
| image | varchar(512) | | |
| image_mobile | varchar(512) | ✓ | iOS/mobile |
| link_url | varchar(512) | ✓ | |
| is_active | bool | | |
| sort_order | int | | |
| created_at / updated_at | | | |

### 3.12. `content_home_advantage`

| Колонка | Тип | Null | Примітка |
|---|---|---|---|
| id | PK | | |
| title | varchar(255) | | |
| text | text | ✓ | |
| icon | varchar(512) | ✓ | ImageField або код іконки |
| sort_order | int | | |
| is_active | bool | | |
| created_at / updated_at | | | |

### 3.13. `content_blog_post`

| Колонка | Тип | Null | Примітка |
|---|---|---|---|
| id | PK | | |
| title | varchar(255) | | |
| slug | varchar(160) | | unique → `/blog/{slug}/` |
| excerpt | text | ✓ | картка в лістингу |
| body | text | | WYSIWYG (абзаци, списки, зображення) |
| cover_image | varchar(512) | ✓ | головне зображення |
| is_published | bool | | |
| published_at | timestamptz | ✓ | |
| seo_title / seo_description / seo_keywords | | ✓ | |
| created_at / updated_at | | | |

Індекси: `(is_published, published_at DESC)`, unique `(slug)`.

### 3.14. `content_contact_lead`

| Колонка | Тип | Null | Примітка |
|---|---|---|---|
| id | PK | | |
| name | varchar(255) | | * обовʼязкове |
| phone | varchar(32) | | * обовʼязкове |
| email | varchar(254) | ✓ | опційно |
| message | text | | * обовʼязкове |
| source_url | varchar(512) | ✓ | |
| is_processed | bool | | default false |
| email_sent_at | timestamptz | ✓ | |
| created_at | | | |

Індекс: `(is_processed, created_at DESC)`.  
Валідація обовʼязкових — у `create_contact_lead` (не лише у формі).

---

### 3.15. `notifications_email_log` (опційно, рекомендовано)

| Колонка | Тип | Примітка |
|---|---|---|
| id | PK | |
| kind | varchar(32) | `order` \| `contact_lead` |
| to_email | varchar(254) | |
| subject | varchar(255) | |
| payload | jsonb | ✓ короткий контекст |
| status | varchar(20) | `sent` \| `failed` |
| error | text | ✓ |
| object_id | varchar(64) | ✓ order.number / lead.id |
| created_at | | |

### 3.16. `seo_redirect_301` (опційно)

| Колонка | Тип | Примітка |
|---|---|---|
| id | PK | |
| old_path | varchar(512) | unique |
| new_path | varchar(512) | |
| is_active | bool | |
| created_at | | |

Legacy URL на старті немає — таблиця для майбутніх змін слагів.

---

## 4. Enums у коді (не CRUD-таблиці)

| Enum | Значення |
|---|---|
| `ProductAvailability` | `in_stock`, `on_order`, `out_of_stock`, `call` |
| `CartStatus` | `active`, `converted`, `abandoned` |
| `OrderStatus` | `new`, `processing`, `completed`, `cancelled` |
| `ShippingMethod` | `pickup`, `delivery`, `nova_poshta` |
| `DeliveryMode` | `warehouse`, `doors` (для `shipping_method=delivery`) |
| `PaymentMethod` | `invoice`, `cash` |
| `EmailKind` | `order`, `contact_lead` |

---

## 5. Verify-матриця (ТЗ / карта ↔ схема)

### 5.1. З карти сайту (URL)

| Вимога | Покриття | Статус |
|---|---|---|
| `/` банер, категорії, переваги | `home_banner`, `home_advantage`, `category` | ✅ |
| `/katalog/` + `/katalog/{slug}/…` | `category`, `product.category_id` | ✅ |
| `/tovar/{slug}/` галерея, ціна/статус, «Купити» | `product`, `product_image`, `cart*` | ✅ |
| `/poshuk/?q=` | пошук по `product.name` / `sku` (сервіс) | ✅ |
| `/koshyk/` | `cart`, `cart_item` | ✅ |
| `/oformlennya/` 3 кроки + сайдбар | `order` поля + сервіси commerce | ✅ |
| Екран подяки (стан) | view state, без окремої таблиці | ✅ |
| `/blog/`, `/blog/{slug}/` | `blog_post` | ✅ |
| `/kontakty/` карта + ЗЗ | `site_settings` + `contact_lead` | ✅ |
| `/sitemap.xml`, `/robots.txt` | seo views + `site_settings.robots_txt` | ✅ |
| Sticky header / лічильник кошика | session cart + context processor | ✅ (код) |

### 5.2. З ТЗ

| § | Вимога | Покриття | Статус |
|---|---|---|---|
| 2.5 | sitemap / robots / ЧПУ | `seo` + slug-и | ✅ |
| 3 | Каталог CRUD кат/підкат/товари | `category` parent, `product` | ✅ |
| 3 | Ціна або статус | `price_uah` + `availability` (+ label) | ✅ |
| 3 | Галерея | `product_image` | ✅ |
| 3 | Кошик HTMX, qty | `cart_item.qty` | ✅ |
| 3 | Checkout: ПІБ*, тел*, email, компанія | `order.customer_*` | ✅ |
| 3 | Доставка 3 способи + НП місто/відд. | `shipping_method` + `np_*` | ✅ |
| 3 | Delivery місто/склад або двері | `delivery_mode` + `delivery_*` + sync | ✅ |
| 3 | Коментар | `customer_comment` | ✅ |
| 3 | Підтвердження + інфо оплати | `payment_method` | ✅ |
| 3 | БД + Email адміну | `order` + `notifications` | ✅ |
| 3 | Блог WYSIWYG + cover | `blog_post` | ✅ |
| 4.1 | Email only | `notify_email`, без Telegram | ✅ |
| 4.2 | Без онлайн-оплати / без вартості НП | немає payments; shipping_uah немає | ✅ |
| 5.1 | Зміни ≤1 хв на вітрині | кеш-інвалідація (код) | ✅ (код) |
| 5.2 | Заявки в адмінці | `order` + `contact_lead` | ✅ |
| 5.3 | Блоки / контакти | `home_*`, `site_settings` | ✅ |
| 7.1 | GTM/GA4 | поля в `site_settings` | ✅ |
| — | Окремі інфо-сторінки поза ТЗ | не створюємо | ✅ |
| — | Кабінет / auth клієнта | не створюємо | ✅ |
| — | ТТН НП / Delivery · calc вартості | backlog | backlog |

### 5.3. Модулі roadmap

| Фаза | У ядрі міграцій |
|---|---|
| M0 Вітрина | `catalog` + `content` (+ banner/advantage/blog) |
| M1 Комерція | `commerce` + `notifications` |
| M2 Доставка | sync НП + Delivery довідників + snapshot на order + search з БД |
| M3 Адмінка | ModelAdmin / Unfold — без нових таблиць |
| M4 SEO | seo views + поля mixin + robots |
| M5 Аналітика | IDs у settings — без таблиць |
| Backlog | ТТН (НП/Delivery), calc вартості, Telegram, payments, сторінки поза ТЗ |

---

## 6. Анти-патерни (Soliron)

1. Не створювати `pricing` / `payments` «на виріст».  
2. Не MTI User / не `accounts` для staff-only.  
3. Не polymorphic SEO-таблиця — лише mixin-колонки.  
4. Не плутати адмін-меню з кількістю apps.  
5. Не рахувати вартість доставки (НП/Delivery) і не писати ТТН у MVP ТЗ.  
6. Не додавати `is_in_stock` поруч із `availability` (ERR-SCHEMA-07).  
7. Не викликати live Delivery API на page load checkout — лише локальна БД після cron sync.

---

## 7. Наступний крок

1. ~~Scaffold + sync НП~~ ✅  
2. ~~Delivery sync + checkout snapshot (без calc/ТТН)~~ ✅  
3. ~~Cron shipping sync~~ ✅ `deploy/sync_shipping.sh` + Docker service `cron` (03:00)  
4. Sitemap-coverage verify по `solironsitemap.pdf` (за потреби)  


**Ще відкрито:** —  
`email_log` + `redirect_301` включені в ядро (scaffold 2026-07-30).
