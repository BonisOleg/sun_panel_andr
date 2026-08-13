"""Віджети адмінки: читабельні file/image inputs під Unfold."""

from __future__ import annotations

from unfold.widgets import UnfoldAdminImageFieldWidget


class ClearableImageInput(UnfoldAdminImageFieldWidget):
    """
    Стилізоване поле зображення Unfold:
    превʼю + окрема кнопка Upload (іконка), без злиття з текстом.
    """

    clear_checkbox_label = "Очистити / видалити зображення"
    initial_text = "Зараз"
    input_text = "Обрати фото"

    def __init__(self, attrs: dict | None = None) -> None:
        merged = {"accept": "image/*"}
        if attrs:
            merged.update(attrs)
        # Превʼю Unfold спрацьовує лише при accept == image/*
        merged["accept"] = "image/*"
        super().__init__(attrs=merged)


class LogoClearableImageInput(ClearableImageInput):
    """Логотип сайту: очищення повертає оригінал зі static."""

    clear_checkbox_label = "Повернути оригінальний логотип Soliron"
    input_text = "Замінити логотип"
