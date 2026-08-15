"""Сигналы приложения api: отправка уведомлений о заказах."""

from django.conf import settings
from django.core.mail import send_mail
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Order


@receiver(post_save, sender=Order)
def notify_admin_about_order(sender, instance, created, **kwargs):
    """Отправляет администратору письмо о новом заказе."""
    if not created:
        return
    if not settings.EMAIL_HOST_USER or not settings.ADMIN_EMAIL:
        return
    subject = f'Новый заказ №{instance.pk} — {instance.status}'
    lines = [
        f'Заказ №{instance.pk}',
        f'Клиент: {instance.user}',
        f'Сумма: {instance.total_price}',
        f'Адрес: {instance.street}, {instance.house}',
    ]
    if instance.comment:
        lines.append(f'Комментарий: {instance.comment}')
    message = '\n'.join(lines)
    send_mail(subject, message, settings.EMAIL_HOST_USER, [settings.ADMIN_EMAIL])
