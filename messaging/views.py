import json
import secrets
import logging
import requests
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from base.decorators import required_permission
from messaging.models import TelegramIntegration
from messaging.forms import TelegramIntegrationForm

logger = logging.getLogger(__name__)


def send_telegram_confirmation(chat_id, message=None):
    """Sends a confirmation or custom message to the Telegram user."""
    bot_token = getattr(settings, "TELEGRAM_BOT_TOKEN", "")
    if not bot_token:
        logger.warning("TELEGRAM_BOT_TOKEN is not configured. Cannot send Telegram message.")
        return False, "TELEGRAM_BOT_TOKEN is not configured."

    if not message:
        message = (
            "🎉 *Connection Successful!*\n\n"
            "Your Telegram account has been successfully linked to your Finance app.\n"
            "You will now receive automated EMI payment reminders here."
        )

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}

    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            logger.info(f"Sent Telegram message to chat_id: {chat_id}")
            return True, "Success"
        else:
            try:
                res_data = response.json()
                description = res_data.get("description", "Unknown error")
            except Exception:
                description = response.text
            logger.error(
                f"Failed to send Telegram message. Status code: {response.status_code}, Response: {response.text}"
            )
            return False, description
    except requests.exceptions.Timeout:
        logger.error("Connection to Telegram timed out.")
        return False, "Request to Telegram timed out. Please try again."
    except requests.exceptions.RequestException as e:
        logger.exception(f"Network error sending Telegram message: {e}")
        return False, "Failed to connect to Telegram servers. Please verify your connection."
    except Exception as e:
        logger.exception(f"Error sending Telegram message: {e}")
        return False, f"Internal error: {str(e)}"



@required_permission("messaging.change_telegramintegration")
def telegram_settings_view(request):
    """
    View to display and manage Telegram integration settings.
    """
    integration, created = TelegramIntegration.objects.get_or_create(user=request.user)

    if request.method == "POST":
        form = TelegramIntegrationForm(request.POST, instance=integration)
        if form.is_valid():
            new_chat_id = form.cleaned_data.get("chat_id")
            old_chat_id = form.initial.get("chat_id")
            integration = form.save(commit=False)
            if new_chat_id:
                integration.is_active = True
                integration.save()
                if new_chat_id != old_chat_id:
                    success, reason = send_telegram_confirmation(new_chat_id)
                    if not success:
                        if "chat not found" in reason.lower():
                            messages.warning(
                                request,
                                "Settings saved, but the bot could not contact you. "
                                "Make sure you have started a chat with `@Clown_finance_bot` in Telegram."
                            )
                        else:
                            messages.warning(
                                request,
                                f"Settings saved, but the confirmation message failed: {reason}"
                            )
                    else:
                        messages.success(request, "Telegram settings updated and confirmation message sent successfully!")
                else:
                    messages.success(request, "Telegram settings updated successfully.")
            else:
                integration.is_active = False
                integration.save()
                messages.success(request, "Telegram connection disconnected.")
            return redirect("messaging:telegram_settings")
    else:
        form = TelegramIntegrationForm(instance=integration)

    context = {
        "active_page": "telegram_settings",
        "form": form,
        "integration": integration,
        "bot_username": getattr(settings, "TELEGRAM_BOT_USERNAME", "FinanceTrackerBot"),
        "has_bot_token": bool(getattr(settings, "TELEGRAM_BOT_TOKEN", "")),
    }
    return render(request, "messaging/settings.html", context)


@required_permission("messaging.change_telegramintegration")
def send_test_message_view(request):
    """
    Sends a manual test message to the user's connected Telegram chat_id.
    """
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "Invalid request method."}, status=405)

    try:
        integration = TelegramIntegration.objects.get(user=request.user)
        if not integration.chat_id or not integration.is_active:
            return JsonResponse({"status": "error", "message": "Telegram is not connected yet."})

        bot_token = getattr(settings, "TELEGRAM_BOT_TOKEN", "")
        if not bot_token:
            return JsonResponse({"status": "error", "message": "TELEGRAM_BOT_TOKEN is not configured in .env file."})

        test_message = "🔔 *Test Message*\n\nYour connection to the Finance app is active and working perfectly!"
        success, reason = send_telegram_confirmation(integration.chat_id, message=test_message)
        if success:
            return JsonResponse({"status": "success", "message": "Test message sent successfully!"})
        else:
            if "chat not found" in reason.lower():
                user_friendly_error = (
                    "Failed to send message: Chat not found. "
                    "Please ensure you have opened a chat with your bot in Telegram and clicked the 'Start' button."
                )
            else:
                user_friendly_error = f"Failed to send message: {reason}"
            return JsonResponse({"status": "error", "message": user_friendly_error})
    except TelegramIntegration.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Telegram integration not found."})




def generate_telegram_link(user):
    """
    Utility function to generate a secure, random link_token for a user,
    saves it to their TelegramIntegration record, and returns a Telegram deep link.
    """
    token = secrets.token_urlsafe(32)
    # Get or create the integration record for the user
    integration, created = TelegramIntegration.objects.get_or_create(user=user)
    integration.link_token = token
    # Reset is_active and chat_id when requesting a new link token
    integration.is_active = False
    integration.chat_id = None
    integration.save()

    bot_username = getattr(settings, "TELEGRAM_BOT_USERNAME", "FinanceTrackerBot")
    return f"https://t.me/{bot_username}?start={token}"


@required_permission("messaging.change_telegramintegration")
def get_telegram_link_view(request):
    """
    View to generate a secure link token and return the Telegram deep link.
    Requires change_telegramintegration permission.
    """
    link = generate_telegram_link(request.user)
    return JsonResponse({"status": "success", "link": link})


@csrf_exempt
def telegram_webhook(request):
    """
    Webhook endpoint to handle incoming updates from Telegram API.
    Always returns HTTP 200 to prevent retries.
    """
    if request.method != "POST":
        return HttpResponse(status=405)

    try:
        data = json.loads(request.body)
        logger.debug(f"Received Telegram webhook payload: {data}")

        message = data.get("message", {})
        text = message.get("text", "")
        chat_id = message.get("chat", {}).get("id")

        if text and text.startswith("/start "):
            # Extract the token following '/start '
            token = text.split(" ", 1)[1].strip()
            if token:
                try:
                    integration = TelegramIntegration.objects.get(link_token=token)
                    integration.chat_id = str(chat_id)
                    integration.is_active = True
                    integration.link_token = None  # Invalidate token after first use
                    integration.save()
                    logger.info(
                        f"Successfully linked Telegram chat_id {chat_id} to user {integration.user}"
                    )
                    send_telegram_confirmation(str(chat_id))
                except TelegramIntegration.DoesNotExist:
                    logger.warning(
                        f"Telegram link token {token} not found or already used."
                    )
    except Exception as e:
        logger.error(f"Error parsing Telegram webhook: {e}")

    # CRITICAL: Always return 200 OK regardless of success or failure
    return HttpResponse(status=200)


@required_permission("messaging.change_telegramintegration")
def reset_telegram_integration_view(request):
    """
    Resets/disconnects the Telegram integration for the current user.
    """
    if request.method != "POST":
        return redirect("messaging:telegram_settings")

    try:
        integration = TelegramIntegration.objects.get(user=request.user)
        integration.chat_id = None
        integration.link_token = None
        integration.is_active = False
        integration.save()
        messages.success(request, "Telegram integration reset successfully.")
    except TelegramIntegration.DoesNotExist:
        messages.error(request, "No Telegram integration found to reset.")

    return redirect("messaging:telegram_settings")

