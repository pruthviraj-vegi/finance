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

    # 1. Calculate target due date (unpaid items due on or before 3 days from today)
    today = timezone.now().date()
    target_due_date = today + timedelta(days=3)

    # 2. Query the database for unpaid, active recurring payments due on or before target due date
    # where the associated user has an active Telegram integration.
    payments = RecurringPayment.objects.filter(
        due_date__lte=target_due_date,
        paid=False,
        recurring_item__active=True,
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
        item_type = item.type

        # Calculate days remaining dynamically
        days_until_due = (payment.due_date - today).days
        if days_until_due == 0:
            due_str = "due *today*"
        elif days_until_due == 1:
            due_str = "due *tomorrow*"
        elif days_until_due > 1:
            due_str = f"due in *{days_until_due} days*"
        else:
            due_str = f"*overdue* by *{-days_until_due} days*"

        # Determine appropriate title and text depending on the type of recurring item
        if item_type == RecurringItem.TypeChoices.EMI:
            title = "EMI Reminder"
            intro = f"You have an upcoming EMI payment {due_str}"
        elif item_type == RecurringItem.TypeChoices.SUBSCRIPTION:
            title = "Subscription Reminder"
            intro = f"You have an upcoming subscription payment {due_str}"
        elif item_type == RecurringItem.TypeChoices.RENEWAL:
            title = "Renewal Reminder"
            intro = f"You have an upcoming renewal payment {due_str}"
        else:
            title = "Payment Reminder"
            intro = f"You have an upcoming payment {due_str}"

        # Formatted Markdown message
        message = (
            f"📅 *{title}*\n\n"
            f"Hello {user.first_name or 'there'},\n"
            f"{intro}:\n\n"
            f"• *Item:* {item.name}\n"
            f"• *Amount:* ₹{payment.amount}\n"
            f"• *Due Date:* {payment.due_date.strftime('%d-%b-%Y')}\n"
            f"• *Period:* {payment.period_label}\n"
        )

        # Include remaining installments only for EMIs
        if item_type == RecurringItem.TypeChoices.EMI:
            installments_remaining = (
                (item.total_installments - item.installments_paid)
                if (
                    item.total_installments is not None
                    and item.installments_paid is not None
                )
                else "N/A"
            )
            message += f"• *Remaining Installments:* {installments_remaining}\n"

        message += (
            f"\nPlease ensure to keep sufficient balance or make the payment soon!"
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
