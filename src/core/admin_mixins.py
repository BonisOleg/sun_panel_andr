"""Адмін-міксіни: TinyMCE для довгих текстових полів (Unfold + django-tinymce)."""

from __future__ import annotations

from tinymce.widgets import TinyMCE


class TinyMCEAdminMixin:
    """
    Явно ставить віджет TinyMCE — Unfold інакше лишає звичайний textarea.
    tinymce_fields — імена полів моделі з довгим текстом.
    """

    tinymce_fields: tuple[str, ...] = ()
    tinymce_height: int = 520

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name in self.tinymce_fields:
            kwargs["widget"] = TinyMCE(
                mce_attrs={
                    "height": self.tinymce_height,
                }
            )
        return super().formfield_for_dbfield(db_field, request, **kwargs)


class TinyMCEShortAdminMixin(TinyMCEAdminMixin):
    """Коротший редактор для subtitle / text / address."""

    tinymce_height: int = 280
