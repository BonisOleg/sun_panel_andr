"""Добити сповіщення, які фоновий потік не встиг надіслати (рестарт воркера).

Беремо замовлення/ліди за останні 24 год, старші 5 хв, де канал не має
ні *_sent_at, ні жодного запису в EmailLog (тобто спроби не було взагалі).
Невдалі спроби (FAILED у логах) не повторюємо — як і раніше.
"""

from __future__ import annotations

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from src.commerce.models import Order
from src.content.models import ContactLead
from src.notifications.models import EmailLog
from src.notifications.services import (
    deliver_lead_notifications,
    deliver_order_notifications,
)


def _never_tried(kind: str, object_id: str, channel: str) -> bool:
    return not EmailLog.objects.filter(kind=kind, object_id=object_id, channel=channel).exists()


class Command(BaseCommand):
    help = "Надіслати Telegram/Email для замовлень і лідів, де відправку не було виконано."

    def handle(self, *args, **options):
        now = timezone.now()
        window = {"created_at__gte": now - timedelta(hours=24), "created_at__lte": now - timedelta(minutes=5)}
        sent = 0
        for order in Order.objects.filter(**window).only("pk", "number", "email_sent_at", "telegram_sent_at"):
            channels = []
            if not order.telegram_sent_at and _never_tried(EmailLog.Kind.ORDER, order.number, "telegram"):
                channels.append("telegram")
            if not order.email_sent_at and _never_tried(EmailLog.Kind.ORDER, order.number, "email"):
                channels.append("email")
            if channels:
                deliver_order_notifications(order.pk, channels=tuple(channels))
                sent += 1
        for lead in ContactLead.objects.filter(**window).only("pk", "email_sent_at", "telegram_sent_at"):
            oid = str(lead.pk)
            channels = []
            if not lead.telegram_sent_at and _never_tried(EmailLog.Kind.CONTACT_LEAD, oid, "telegram"):
                channels.append("telegram")
            if not lead.email_sent_at and _never_tried(EmailLog.Kind.CONTACT_LEAD, oid, "email"):
                channels.append("email")
            if channels:
                deliver_lead_notifications(lead.pk, channels=tuple(channels))
                sent += 1
        self.stdout.write(f"pending notifications processed: {sent}")
