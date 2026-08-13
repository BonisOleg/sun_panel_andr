"""Завантаження зображень TinyMCE для статей блогу."""

from __future__ import annotations

import uuid
from pathlib import Path

from django.contrib.admin.views.decorators import staff_member_required
from django.core.files.storage import default_storage
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from src.content.image_processing import (
    BLOG_IMAGE_EXTENSIONS,
    process_uploaded_blog_image,
)


@staff_member_required
@require_POST
def tinymce_blog_image_upload(request):
    uploaded = request.FILES.get("file")
    if uploaded is None:
        return JsonResponse({"error": "Файл не передано"}, status=400)

    try:
        processed = process_uploaded_blog_image(uploaded)
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    except OSError:
        return JsonResponse({"error": "Не вдалося прочитати зображення"}, status=400)

    ext = Path(processed.name).suffix.lstrip(".").lower() or "jpg"
    if ext not in BLOG_IMAGE_EXTENSIONS:
        ext = "jpg"
    dest = f"content/blog/inline/{uuid.uuid4().hex}.{ext}"
    saved_name = default_storage.save(dest, processed)
    return JsonResponse({"location": default_storage.url(saved_name)})
