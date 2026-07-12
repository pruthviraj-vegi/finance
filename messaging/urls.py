from django.urls import path
from messaging.views import (
    get_telegram_link_view,
    telegram_webhook,
    telegram_settings_view,
    send_test_message_view,
    reset_telegram_integration_view,
)

app_name = "messaging"

urlpatterns = [
    path("settings/", telegram_settings_view, name="telegram_settings"),
    path("link/", get_telegram_link_view, name="telegram_link"),
    path("webhook/", telegram_webhook, name="telegram_webhook"),
    path("test-message/", send_test_message_view, name="send_test_message"),
    path("reset/", reset_telegram_integration_view, name="reset_telegram"),
]


