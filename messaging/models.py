from django.db import models
from django.conf import settings


class TelegramIntegration(models.Model):
    """
    Model to store Telegram integration credentials for a User.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="telegram_integration",
        verbose_name="User",
    )
    chat_id = models.CharField(
        max_length=50, null=True, blank=True, verbose_name="Telegram Chat ID"
    )
    link_token = models.CharField(
        max_length=64, unique=True, null=True, blank=True, verbose_name="Link Token"
    )
    is_active = models.BooleanField(default=False, verbose_name="Is Active")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    def __str__(self):
        return f"Telegram Integration for {self.user}"

    class Meta:
        verbose_name = "Telegram Integration"
        verbose_name_plural = "Telegram Integrations"
        ordering = ["-created_at"]
