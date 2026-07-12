from django import forms
from messaging.models import TelegramIntegration


class TelegramIntegrationForm(forms.ModelForm):
    """Form to manage Telegram integration settings."""

    class Meta:
        model = TelegramIntegration
        fields = ["chat_id"]
        widgets = {
            "chat_id": forms.TextInput(
                attrs={
                    "class": "form-input",
                    "placeholder": "e.g., 987654321",
                }
            ),
        }

    def clean_chat_id(self):
        chat_id = self.cleaned_data.get("chat_id")
        if chat_id:
            chat_id = chat_id.strip()
            if not chat_id.isdigit():
                raise forms.ValidationError(
                    "Telegram Chat ID must consist of digits only."
                )
        return chat_id
