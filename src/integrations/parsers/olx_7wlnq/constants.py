from pathlib import Path

SOURCE = "olx_7wlnq"
SELLER_ID = "7wLNQ"
SELLER_LIST_URL = "https://www.olx.ua/uk/list/user/7wLNQ/"
BASE_ORIGIN = "https://www.olx.ua"

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

REQUEST_TIMEOUT = 30
MAX_RETRIES = 3
DELAY_SEC = 0.6
DELAY_IMAGE_SEC = 0.25

PLACEHOLDER_IMAGE_MARKERS = (
    "no_thumbnail",
    "no-photo",
    "placeholder",
)

# Breadcrumb-регіональні хвости OLX — не є товарними категоріями
REGION_BREADCRUMB_MARKERS = (
    "область",
    "район",
    " - Полтава",
    " - Київ",
    " - Харків",
    " - Львів",
    "Печерський",
    "Київський",
    "Личаківський",
)


def data_root(base_dir: Path) -> Path:
    return base_dir / "data" / SOURCE


def products_dir(base_dir: Path) -> Path:
    return data_root(base_dir) / "products"


def images_dir(base_dir: Path) -> Path:
    return data_root(base_dir) / "images"


def categories_path(base_dir: Path) -> Path:
    return data_root(base_dir) / "categories" / "tree.json"


def manifest_path(base_dir: Path) -> Path:
    return data_root(base_dir) / "run_meta.json"
