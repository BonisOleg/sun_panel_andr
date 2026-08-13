"""Латинські / розмовні аліаси міст → українська назва для пошуку Delivery."""

from __future__ import annotations

# Ключ — нижній регістр (latin/uk). Значення — фрагмент укр. назви для contains.
CITY_ALIASES: dict[str, str] = {
    # Київ
    "kyiv": "київ",
    "kiev": "київ",
    "киев": "київ",
    # Одеса
    "odesa": "одеса",
    "odessa": "одеса",
    "одесса": "одеса",
    # Харків
    "kharkiv": "харків",
    "kharkov": "харків",
    "харьков": "харків",
    # Львів
    "lviv": "львів",
    "lvov": "львів",
    "львов": "львів",
    # Дніпро
    "dnipro": "дніпро",
    "dnepr": "дніпро",
    "dnipropetrovsk": "дніпро",
    "днепр": "дніпро",
    "днепропетровск": "дніпро",
    # Запоріжжя
    "zaporizhzhia": "запоріжжя",
    "zaporizhia": "запоріжжя",
    "zaporozhye": "запоріжжя",
    "запорожье": "запоріжжя",
    # Вінниця
    "vinnytsia": "вінниця",
    "vinnitsa": "вінниця",
    "винница": "вінниця",
    # Полтава
    "poltava": "полтава",
    # Суми
    "sumy": "суми",
    # Чернігів
    "chernihiv": "чернігів",
    "chernigov": "чернігів",
    "чернигов": "чернігів",
    # Черкаси
    "cherkasy": "черкаси",
    "cherkassy": "черкаси",
    # Чернівці
    "chernivtsi": "чернівці",
    "chernovtsy": "чернівці",
    "черновцы": "чернівці",
    # Хмельницький
    "khmelnytskyi": "хмельницький",
    "khmelnitsky": "хмельницький",
    # Івано-Франківськ
    "ivano-frankivsk": "івано-франківськ",
    "ivano frankivsk": "івано-франківськ",
    # Тернопіль
    "ternopil": "тернопіль",
    "ternopol": "тернопіль",
    # Рівне
    "rivne": "рівне",
    "rovno": "рівне",
    "ровно": "рівне",
    # Луцьк
    "lutsk": "луцьк",
    # Ужгород
    "uzhhorod": "ужгород",
    "uzhgorod": "ужгород",
    # Миколаїв
    "mykolaiv": "миколаїв",
    "nikolaev": "миколаїв",
    "николаев": "миколаїв",
    # Херсон
    "kherson": "херсон",
    # Кривий Ріг
    "kryvyi rih": "кривий ріг",
    "krivoy rog": "кривий ріг",
    "кривой рог": "кривий ріг",
    # Кропивницький
    "kropyvnytskyi": "кропивницький",
    "kirovograd": "кропивницький",
    "кіровоград": "кропивницький",
    # Житомир
    "zhytomyr": "житомир",
    "zhitomir": "житомир",
    # Біла Церква
    "bila tserkva": "біла церква",
    # Мукачево
    "mukachevo": "мукачево",
    # Кам'янець-Подільський
    "kamianets-podilskyi": "кам'янець-подільський",
    "kamenets-podolsk": "кам'янець-подільський",
}


def expand_city_query(query: str) -> list[str]:
    """Повертає варіанти пошуку (casefold) включно з аліасами."""
    raw = (query or "").strip()
    if not raw:
        return []
    q = raw.casefold()
    terms: set[str] = {q}

    if q in CITY_ALIASES:
        terms.add(CITY_ALIASES[q].casefold())

    # Частковий збіг латинського аліаса (ky → kyiv → київ)
    for alias, uk in CITY_ALIASES.items():
        if alias.startswith(q) or q.startswith(alias):
            terms.add(alias)
            terms.add(uk.casefold())

    return [t for t in terms if len(t) >= 2]
