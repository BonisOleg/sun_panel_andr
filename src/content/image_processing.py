"""Обробка зображень блогу: розширення + center-crop при надмірному розмірі."""

from __future__ import annotations

import io
from pathlib import Path

from django.core.files.base import ContentFile
from django.core.files.uploadedfile import UploadedFile
from PIL import Image, ImageOps

BLOG_IMAGE_EXTENSIONS = ("jpg", "jpeg", "png", "webp")
BLOG_IMAGE_ACCEPT = ".jpg,.jpeg,.png,.webp,image/jpeg,image/png,image/webp"
BLOG_COVER_WIDTH = 1200
BLOG_COVER_HEIGHT = 900
BLOG_COVER_HELP = (
    "Обкладинка картки та шапки статті. "
    f"Дозволені формати: {', '.join(BLOG_IMAGE_EXTENSIONS)}. "
    f"Якщо фото більше за {BLOG_COVER_WIDTH}×{BLOG_COVER_HEIGHT} px — "
    "автоматично обрізається по центру до 4:3. "
    "Щоб видалити — «Очистити / видалити зображення» → Зберегти."
)
BLOG_BODY_IMAGE_HELP = (
    f"У тексті (WYSIWYG) дозволені: {', '.join(BLOG_IMAGE_EXTENSIONS)}. "
    f"Завеликі фото обрізаються до {BLOG_COVER_WIDTH}×{BLOG_COVER_HEIGHT} (4:3)."
)

_FORMAT_BY_EXT = {
    "jpg": "JPEG",
    "jpeg": "JPEG",
    "png": "PNG",
    "webp": "WEBP",
}


def extension_of(name: str) -> str:
    return Path(name or "").suffix.lstrip(".").lower()


def is_allowed_blog_image(name: str) -> bool:
    return extension_of(name) in BLOG_IMAGE_EXTENSIONS


def _save_format(ext: str) -> str:
    return _FORMAT_BY_EXT.get(ext, "JPEG")


def center_crop_if_oversized(
    source,
    *,
    max_width: int = BLOG_COVER_WIDTH,
    max_height: int = BLOG_COVER_HEIGHT,
    filename: str = "image.jpg",
) -> ContentFile | None:
    """
    Якщо ширина або висота перевищує ліміт — center-crop 4:3 і resize до max.
    Інакше повертає None (файл без змін).
    """
    source.seek(0)
    with Image.open(source) as img:
        img = ImageOps.exif_transpose(img)
        width, height = img.size
        if width <= max_width and height <= max_height:
            return None

        target_ratio = max_width / max_height
        current_ratio = width / height if height else target_ratio

        if current_ratio > target_ratio:
            crop_h = height
            crop_w = int(round(height * target_ratio))
        else:
            crop_w = width
            crop_h = int(round(width / target_ratio))

        left = max(0, (width - crop_w) // 2)
        top = max(0, (height - crop_h) // 2)
        cropped = img.crop((left, top, left + crop_w, top + crop_h))
        resized = cropped.resize((max_width, max_height), Image.Resampling.LANCZOS)

        ext = extension_of(filename) or "jpg"
        fmt = _save_format(ext)
        if fmt == "JPEG" and resized.mode not in {"RGB", "L"}:
            resized = resized.convert("RGB")
        elif fmt == "PNG" and resized.mode == "P":
            resized = resized.convert("RGBA")

        buffer = io.BytesIO()
        save_kwargs: dict = {}
        if fmt == "JPEG":
            save_kwargs.update(quality=88, optimize=True)
        elif fmt == "WEBP":
            save_kwargs.update(quality=88, method=4)
        resized.save(buffer, format=fmt, **save_kwargs)
        buffer.seek(0)

        out_name = Path(filename).stem + f".{ext if ext in BLOG_IMAGE_EXTENSIONS else 'jpg'}"
        return ContentFile(buffer.getvalue(), name=out_name)


def process_uploaded_blog_image(uploaded: UploadedFile) -> ContentFile:
    """Валідує розширення та обрізає завелике зображення для TinyMCE / поля."""
    name = getattr(uploaded, "name", "") or "image.jpg"
    if not is_allowed_blog_image(name):
        allowed = ", ".join(BLOG_IMAGE_EXTENSIONS)
        raise ValueError(f"Дозволені формати: {allowed}")

    processed = center_crop_if_oversized(uploaded, filename=name)
    if processed is not None:
        return processed

    uploaded.seek(0)
    return ContentFile(uploaded.read(), name=Path(name).name)
