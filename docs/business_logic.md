# Soliron — бізнес-логіка (URL → controllers → data flow)

**Версія:** 1.2 · **Дата:** 2026-08-04 · **Статус:** LOCK (мікро-рішення)  
**Джерела:** `Технічне_завдання_Голінковський.docx` · `solironsitemap.pdf` v1.1 · `tables.md` v1.2  
**Регламент:** Prometey `ecommerce_business_logic_skill` · `novaposhta_skill` · шари `selectors` / `services` / thin `views`  
**Стек:** Django 5+ · HTMX · session-cart · guest checkout · Email only · НП/Delivery без ТТН/вартості

---

## 0. Принципи (lock)

| Правило | Як у Soliron |
|---|---|
| Read vs write | `selectors.py` — лише queryset/фільтри; `services.py` — мутації + `@transaction.atomic` |
| Views | thin: parse → selector/service → template/HTMX partial |
| Ціна при checkout | **ревалідація з БД** у `place_order()`; `cart_item.unit_price_uah` — лише UI-кеш (SEC-02) |
| Кошик | `session_key`; без User; ownership через session (SEC-01 guest) |
| Auth | лише staff у `ADMIN_URL` (канон `/sol-cabin/`, не `/admin/`); публічних кабінетів немає |
| SiteSettings | `.load()` / `get_or_create`, ніколи `.first()` (ERR-BIZ-07) |
| Склад | у MVP **не** зменшуємо `stock` (немає `stock_qty`); блок «Купити» за `availability` |
| «Купити» | дозволено при `in_stock` / `on_order` / `call` і при `price_uah IS NULL`; ні — лише `out_of_stock` |
| Категорія товару | лише `category_id` (без M2M); фільтр = піддерево |
| НП | кеш `np_city`/`np_warehouse` + sync; autocomplete **з БД** (`novaposhta_skill`) |
| Delivery Auto | кеш `delivery_city`/`delivery_warehouse` + `sync_delivery_data`; autocomplete **з БД**; без calc/ТТН (ТЗ) |
| RBAC менеджера | Django staff + ModelAdmin; окремого `manager_permission` немає в ТЗ |

---

## 1. Мапа URL → controller (усі рядки карти)

| URL / вимога | App.Controller | Selector / Service |
|---|---|---|
| `/` | `content.HomeView` | `home_banners()`, `home_advantages()`, `catalog.active_root_categories()` |
| `/katalog/` | `catalog.CatalogListView` | `filter_products(category=None, q=…)` |
| `/katalog/{slug}/` | `catalog.CategoryListView` | `get_category_by_slug()` → `filter_products(category=…+descendants)` |
| `/tovar/{slug}/` | `catalog.ProductDetailView` | `get_published_product(slug)` + images prefetch |
| POST «Купити» | `commerce.CartAddView` (HTMX) | `add_item(session, product_id, qty)` |
| `/poshuk/?q=` | `catalog.SearchView` | `filter_products(q=…)` → empty «Нічого не знайдено» |
| `/koshyk/` | `commerce.CartDetailView` | `get_active_cart()` + items |
| POST qty / remove | `commerce.CartUpdateView` / `CartRemoveView` | `update_item_qty` / `remove_item` |
| `/oformlennya/` GET | `commerce.CheckoutView` | крок з session; сайдбар = cart selector |
| `/oformlennya/` POST step | `commerce.CheckoutStepView` (HTMX) | валідація кроку → session draft |
| POST підтвердити | `commerce.CheckoutSubmitView` | `place_order()` → email → thank-you state |
| `/blog/` | `content.BlogListView` | `published_posts()` + paginate / «Показати ще» |
| `/blog/{slug}/` | `content.BlogDetailView` | `get_published_post(slug)` |
| `/kontakty/` GET | `content.ContactsView` | `SiteSettings.load()` |
| `/kontakty/` POST | `content.ContactLeadCreateView` (AJAX) | `create_contact_lead()` → email |
| `/api/np/cities/?q=` | `shipping.NPCitiesView` | `search_cities(q)` |
| `/api/np/warehouses/?city=` | `shipping.NPWarehousesView` | `list_warehouses(city_ref)` |
| `/api/delivery/cities/?q=` | `shipping.DeliveryCitiesView` | `delivery.search.search_cities(q)` |
| `/api/delivery/warehouses/?city_id=` | `shipping.DeliveryWarehousesView` | `delivery.search.list_warehouses(city_id)` |
| `/sitemap.xml` | `seo.SitemapIndex` | published products/categories/posts + static |
| `/robots.txt` | `seo.RobotsView` | `SiteSettings.robots_txt` або дефолт |
| 404 / 500 | `core` templates | системні |
| `/sol-cabin/` (`ADMIN_URL`) | Django/Unfold admin | staff CRUD (ТЗ §5); ERR-132 |

Службові HTMX (не в меню): cart badge partial, checkout step partials, blog «Показати ще».

---

## 2. Потік даних по доменах

### 2.1. `catalog` — читання / фільтрація

```
Вітрина:
  Product.objects.filter(is_published=True)
    ± category_id IN (category + descendants)
    ± q: name icontains OR sku icontains   # UA: нормалізація casefold у сервісі пошуку
  order_by: sort_order, -updated_at (дефолт MVP; faceted attrs — backlog)

Категорія:
  get_category_by_slug(slug) → 404 якщо !is_active
  descendants(category) — рекурсія / CTE; товари primary category_id у піддереві

PDP:
  get_published_product(slug).prefetch_related('images')
  display_price = price_uah OR availability_label OR label(availability)
  «Купити» OK якщо availability ∈ {in_stock, on_order, call} (ціна може бути NULL)
  «Купити» BLOCKED лише якщо out_of_stock
```

**Breadcrumbs:** ancestors(category) + product.name.  
**Empty-state:** будь-який порожній queryset → шаблон «Нічого не знайдено» (ТЗ §6.1).

**Публічний контекст (ERR-BIZ-06):** лише name, slug, description, price_uah, availability*, images, category — без внутрішніх адмін-полів.

### 2.2. `commerce` — кошик

```
get_or_create_cart(session_key) → status=active

add_item:
  product = published + availability != out_of_stock
  unit_price_uah = product.price_uah   # snapshot UI; може бути NULL
  upsert CartItem(cart, product); qty += n
  return cart + badge count

update_item_qty / remove_item:
  item scoped by cart(session); qty >= 1 або delete

Контекст-процесор: cart_items_count(session) для sticky header
```

Сесія конвертується в `converted` лише після успішного `place_order`.

### 2.3. `commerce` — checkout (один URL, 3 кроки)

**Стан кроків** у `request.session['checkout']` (не в БД до submit):

| Крок | Поля | Валідація |
|---|---|---|
| 1 | name*, phone*, email, company | phone: digits/+; name required |
| 2 | shipping_method* + (np_* \| delivery_*) + comment | NP: city+warehouse; Delivery: mode+city+(warehouse\|address); pickup: ok |
| 3 | payment_method (`invoice`\|`cash`) + review | підтвердження |

На кожному кроці **сайдбар** = selector кошика (товари, qty, сума; NULL-ціни → рядок «за запитом», subtotal лише по priced items).

```
place_order(session, checkout_draft) @atomic:
  1. cart = active cart; items = select_related('product')
  2. якщо items порожні → CartError
  3. для кожного item: live = product (published?); ревалідація price_uah з БД
  4. створити Order(number, customer_*, shipping_*, payment_method, totals)
  5. OrderItem snapshot (name, sku, qty, unit_price, line_total)
  6. cart.status = converted; clear checkout session
  7. notifications.notify_order(order)  # Email + Telegram; flags email_sent_at / telegram_sent_at
  8. повернути order → view рендерить екран подяки (той самий /oformlennya/)
```

**Номер замовлення:** `SL-YYYYMMDD-XXXX` (унікальність у сервісі).  
**Статуси:** `new` → `processing` → `completed` \| `cancelled` (матриця в admin service за потреби).

### 2.4. `shipping` — Нова Пошта (`novaposhta_skill`)

```
sync_cities / sync_warehouses  (management command):
  Address.getCities / getWarehouses
  Page = str, Limit = "500"; update_or_create за ref

search_cities(q):          # checkout — ЛИШЕ локальна БД
  NPCity.objects.filter(is_active=True, name__icontains=q)[:20]
list_warehouses(city_ref, q=''):
  NPWarehouse.objects.filter(city__ref=city_ref, is_active=True, …)
```

На submit **не** створюємо ТТН. У Order — snapshot refs+names.  
Вартість доставки **не** рахуємо (`total_uah = subtotal_uah`).

### 2.4b. `shipping` — Delivery Auto (ТЗ: без calc / без ТТН)

```
sync_delivery_data (cron / manage.py):
  GetAreasList(fl_all=false) → DeliveryCity
  GetWarehousesList(CityId) → DeliveryWarehouse (is_freight)

search (checkout — ЛИШЕ локальна БД):
  /api/delivery/cities/?q=
  /api/delivery/warehouses/?city_id=&q=

checkout step 2 (shipping_method=delivery):
  delivery_mode = warehouse | doors
  warehouse → city + warehouse snapshot
  doors → city + delivery_address (вулиця+будинок)
```

Env: `DELIVERY_PUBLIC_KEY` / `DELIVERY_SECRET_KEY` / sender warehouse IDs — для майбутнього HMAC (ТТН backlog).  
У MVP **не** викликаємо калькулятор і **не** створюємо квитанцію.  
`total_uah = subtotal_uah`.

**Cron:** `deploy/sync_shipping.sh` (Delivery `--warehouses` + НП `--warehouses`) щодня о **03:00**.  
- Docker: сервіс `cron` + `supercronic` (`deploy/crontab`, `deploy/run_cron.sh`)  
- Локально: user crontab → той самий скрипт; лог `data/logs/shipping_sync.log`

### 2.5. `content` — головна, блог, контакти

```
Home: active banners (sort) + advantages + root categories (is_active, parent IS NULL)
Blog list: is_published + published_at <= now; order -published_at; paginate / load-more HTMX
Blog detail: slug + published else 404; body as safe HTML from TinyMCE
Contacts GET: SiteSettings.load() → phones, email, address, map
Contacts POST AJAX:
  validate name*, phone*, message* (email optional)
  → ContactLead.create → notify_lead → JSON/HTML «Дякуємо»
  без full page reload (ТЗ §6.3)
```

### 2.6. `notifications`

```
notify_order(order) / notify_lead(lead):
  format_*_message() — спільний текст (SKU, qty, суми, контакти, доставка)
  → Email (Resend SMTP через EMAIL_* / notify_email|NOTIFY_EMAIL)
  → Telegram Bot API (TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID, один менеджер)
  → EmailLog на кожен канал (channel=email|telegram)
  Канали незалежні; фейл одного не валить checkout/форму.
```

Прапорці: `Order.email_sent_at` / `telegram_sent_at`, те саме для `ContactLead`.

### 2.7. `seo`

- Sitemap: Category(is_active), Product(is_published), BlogPost(is_published), static `/` `/kontakty/` `/katalog/` `/blog/`
- robots: `Disallow: /sol-cabin/`, `Disallow: /admin/`, `Sitemap: …`
- Resolve SEO: entity.seo_* або fallback title/name

### 2.8. Адмінка (ТЗ §5) — не окремі public controllers

| Дія менеджера | Де живе логіка |
|---|---|
| CRUD category/product/images | ModelAdmin; після save — cache invalidate (≤1 хв) |
| Замовлення / ліди | readonly list+detail; зміна `order.status` / `lead.is_processed` |
| Банери, переваги, контакти, блог WYSIWYG | content ModelAdmin |
| Ключі НП/GTM | env + SiteSettings IDs; секрети не в git |

---

## 3. Фільтри та пошук (деталізація)

| Вхід | Джерело | Обробка |
|---|---|---|
| Категорія (меню / блок головної) | `category.slug` | дерево → queryset товарів піддерева |
| `?q=` на `/poshuk/` або `/katalog/` | GET | `icontains` name + sku; trim; мін. 1 символ |
| Сітка каталогу | — | лише published; без атрибутивних facets у MVP |
| Empty | — | той самий шаблон empty-state |

Сортування MVP: `sort_order`, потім `-updated_at`. Додаткові sort-enums — backlog.

---

## 4. Ланцюжок реалізації (dependency order)

```
1. core + content.SiteSettings.load()   — щоб не падав перший рендер
2. catalog selectors + urls             — M0 вітрина
3. content home/blog/contacts           — M0
4. commerce cart                        — M1
5. shipping NP autocomplete             — M2 (перед checkout step 2)
6. commerce checkout + place_order      — M1/M2
7. notifications email                  — з place_order / lead
8. seo sitemap/robots                   — M4
9. admin Unfold + cache TTL             — M3
10. GTM/GA4 dataLayer hooks             — M5 (фронт-події, не таблиці)
11. sitemap-coverage verify             — завжди останнім
```

---

## 5. Події аналітики (точки в логіці, не app)

| Подія GA4/GTM | Тригер у коді |
|---|---|
| `add_to_cart` | після успішного `add_item` (HTMX response / dataLayer push) |
| `begin_checkout` | GET `/oformlennya/` крок 1 |
| `purchase` / `order_success` | після `place_order` (thank-you) |
| `generate_lead` | після `create_contact_lead` |
| `contact_click` | кліки `tel:` / `mailto:` у шаблоні |

---

## 6. Security checklist (скорочено для Soliron)

| ID | Правило | Soliron |
|---|---|---|
| SEC-01 | ownership | cart/order draft лише за session_key |
| SEC-02 | price | ревалідація в `place_order` |
| SEC-03 | qty | int ≥ 1; верхня межа (напр. 999) у service |
| — | CSRF | усі POST; HTMX csrf |
| — | NP keys | лише env |
| — | XSS | TinyMCE body лише staff; на вітрині `|safe` тільки для довіреного HTML |

Складський race (ERR-BIZ-05) — **поза MVP** (немає stock_qty decrement).

---

## 7. Sitemap-coverage verify (шаблон здачі)

| URL з карти | urls | View | Selector/Service | Навігація | Статус |
|---|---|---|---|---|---|
| `/` | ☐ | ☐ | ☐ | ☐ | |
| `/katalog/` | ☐ | ☐ | ☐ | ☐ | |
| `/katalog/{slug}/…` | ☐ | ☐ | ☐ | ☐ | |
| `/tovar/{slug}/` | ☐ | ☐ | ☐ | ☐ | |
| `/poshuk/?q=` | ☐ | ☐ | ☐ | ☐ | |
| `/koshyk/` | ☐ | ☐ | ☐ | ☐ | |
| `/oformlennya/` (+ thank-you state) | ☐ | ☐ | ☐ | ☐ | |
| `/blog/` | ☐ | ☐ | ☐ | ☐ | |
| `/blog/{slug}/` | ☐ | ☐ | ☐ | ☐ | |
| `/kontakty/` | ☐ | ☐ | ☐ | ☐ | |
| `/api/np/cities/` `/warehouses/` | ☐ | ☐ | ☐ | — | |
| `/sitemap.xml` `/robots.txt` | ☐ | ☐ | ☐ | — | |

Будь-який рядок без статусу після імплементації = блокер (ERR-BIZ-01).

---

## 8. Lock мікро-рішень (2026-07-30)

| # | Рішення |
|---|---|
| 1 | «Купити» при `call` / без ціни — **так** |
| 2 | Лише `category_id` |
| 3 | НП як у vault: кеш + sync; пошук з БД |
| 4 | ЗЗ: `name*` · `phone*` · `message*` · `email` опційно — **затверджено** |

Наступний крок: scaffold / моделі (після рішення по `email_log` / `redirect_301` за бажанням).

