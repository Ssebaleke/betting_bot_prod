from django.db import models
from django.contrib.auth.models import User


class TelegramBotConfig(models.Model):
    """
    Stores Telegram bot tokens managed from Django Admin.
    Only ONE bot should be active at a time.
    """
    name = models.CharField(
        max_length=100,
        help_text="Internal name e.g Vicotech Main Bot"
    )
    bot_token = models.CharField(
        max_length=255,
        help_text="Telegram Bot Token from BotFather"
    )
    is_active = models.BooleanField(
        default=False,
        help_text="Only one bot can be active"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        status = "ACTIVE" if self.is_active else "INACTIVE"
        return f"{self.name} ({status})"


class TelegramProfile(models.Model):
    """
    Links a Django user to a Telegram account.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE
    )
    telegram_id = models.BigIntegerField(
        unique=True
    )
    username = models.CharField(
        max_length=150,
        blank=True,
        null=True
    )
    linked_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.user.username} ↔ {self.telegram_id}"
