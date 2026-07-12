import logging
import requests
from celery import shared_task
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from expense.models import RecurringPayment, RecurringItem

logger = logging.getLogger(__name__)


@shared_task
def send_daily_emi_reminders():
    """
    Celery task to send daily EMI reminders to active Telegram users.
    Sends notifications for EMIs due in exactly 3 days.
    """
    bot_token = getattr(settings, "TELEGRAM_BOT_TOKEN", None)
    if not bot_token:
        logger.error("TELEGRAM_BOT_TOKEN is not configured in settings.")
        return "Telegram Bot Token not configured"

    # 1. Calculate target due date (exactly 3 days from today)
    target_due_date = timezone.now().date() + timedelta(days=3)

    # 2. Query the EMI database for unpaid recurring payments matching target due date
    # where the associated user has an active Telegram integration.
    payments = RecurringPayment.objects.filter(
        recurring_item__type=RecurringItem.TypeChoices.EMI,
        due_date=target_due_date,
        paid=False,
        recurring_item__user__telegram_integration__is_active=True,
    ).select_related(
        "recurring_item",
        "recurring_item__user",
        "recurring_item__user__telegram_integration",
    )

    total_sent = 0
    total_failed = 0
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    # 3. Loop through results and send messages
    for payment in payments:
        user = payment.recurring_item.user
        chat_id = user.telegram_integration.chat_id
        if not chat_id:
            logger.warning(
                f"Active Telegram integration for user {user} is missing chat_id."
            )
            continue

        item = payment.recurring_item
        installments_remaining = (
            (item.total_installments - item.installments_paid)
            if (
                item.total_installments is not None
                and item.installments_paid is not None
            )
            else "N/A"
        )

        # Formatted Markdown message
        message = (
            f"📅 *EMI Reminder*\n\n"
            f"Hello {user.first_name or 'there'},\n"
            f"You have an upcoming EMI payment due in 3 days:\n\n"
            f"• *Item:* {item.name}\n"
            f"• *Amount:* ₹{payment.amount}\n"
            f"• *Due Date:* {payment.due_date.strftime('%d-%b-%Y')}\n"
            f"• *Period:* {payment.period_label}\n"
            f"• *Remaining Installments:* {installments_remaining}\n\n"
            f"Please ensure to keep sufficient balance or make the payment soon!"
        )

        payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}

        # 4. Make HTTP POST request to Telegram API with basic error handling
        try:
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                logger.info(
                    f"EMI reminder successfully sent to {user} (chat_id: {chat_id})"
                )
                total_sent += 1
            else:
                logger.error(
                    f"Failed to send EMI reminder to {user} (chat_id: {chat_id}). "
                    f"Status Code: {response.status_code}, Response: {response.text}"
                )
                total_failed += 1
        except Exception as e:
            logger.exception(
                f"Error occurred while sending EMI reminder to {user} (chat_id: {chat_id}): {e}"
            )
            total_failed += 1

    return f"Completed sending daily EMI reminders. Sent: {total_sent}, Failed: {total_failed}."
