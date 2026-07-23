from django import forms
from base.utility import StringProcessor
from expense.models import Category, Transaction, RecurringItem, RecurringPayment


class CategoryForm(forms.ModelForm):
    """
    Form for creating and editing expense/income Categories.
    """
    class Meta:
        model = Category
        fields = ["name", "color"]
        widgets = {
            "name": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": "e.g. Food, Rent, Entertainment",
                "required": True
            }),
            "color": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": "e.g. #34d399 (Emerald), #f43f5e (Rose)",
                "type": "color"
            }),
        }

    def clean_name(self):
        name = self.cleaned_data.get("name")
        if name:
            return StringProcessor(name).toTitle()
        return name


class TransactionForm(forms.ModelForm):
    """
    Form for creating and editing Transactions.
    """
    class Meta:
        model = Transaction
        fields = ["amount", "type", "category", "date", "note", "recurring_payment"]
        widgets = {
            "amount": forms.TextInput(attrs={
                "class": "form-input indian-number",
                "placeholder": "0.00",
                "required": True
            }),
            "type": forms.RadioSelect(attrs={"class": "segmented-radio-input"}),
            "category": forms.Select(attrs={"class": "form-select", "required": True}),
            "date": forms.DateInput(attrs={
                "class": "form-input",
                "type": "date",
                "required": True
            }),
            "note": forms.Textarea(attrs={
                "class": "form-textarea",
                "placeholder": "Optional transaction note...",
                "rows": 3
            }),
            "recurring_payment": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields["category"].queryset = Category.objects.filter(user=user)
            # Only show recurring payments related to user's recurring items
            self.fields["recurring_payment"].queryset = RecurringPayment.objects.filter(
                recurring_item__user=user
            )

        # Remove blank option '--------' and default type to EXPENSE
        self.fields["type"].choices = Transaction.TypeChoices.choices
        if not self.instance.pk and not self.initial.get("type"):
            self.initial["type"] = Transaction.TypeChoices.EXPENSE

    def clean_amount(self):
        amount = self.cleaned_data.get("amount")
        if amount is not None and amount <= 0:
            raise forms.ValidationError("Amount must be greater than zero.")
        return amount

    def clean_note(self):
        note = self.cleaned_data.get("note")
        if note:
            return StringProcessor(note).toCapitalize()
        return note


class RecurringItemForm(forms.ModelForm):
    """
    Form for creating and editing Recurring Items (subscriptions, EMIs, renewals).
    """
    class Meta:
        model = RecurringItem
        fields = [
            "name", "type", "category", "amount", "frequency",
            "start_date", "end_date", "next_due_date",
            "total_installments", "installments_paid", "active", "notes"
        ]
        widgets = {
            "name": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": "e.g. Netflix, Car Loan EMI",
                "required": True
            }),
            "type": forms.RadioSelect(attrs={"class": "segmented-radio-input"}),
            "category": forms.Select(attrs={"class": "form-select", "required": True}),
            "amount": forms.TextInput(attrs={
                "class": "form-input indian-number",
                "placeholder": "0.00",
                "required": True
            }),
            "frequency": forms.RadioSelect(attrs={"class": "segmented-radio-input"}),
            "start_date": forms.DateInput(attrs={
                "class": "form-input",
                "type": "date",
                "required": True
            }),
            "end_date": forms.DateInput(attrs={
                "class": "form-input",
                "type": "date"
            }),
            "next_due_date": forms.DateInput(attrs={
                "class": "form-input",
                "type": "date",
                "required": True
            }),
            "total_installments": forms.NumberInput(attrs={
                "class": "form-input",
                "placeholder": "e.g. 12 (EMIs only)"
            }),
            "installments_paid": forms.NumberInput(attrs={
                "class": "form-input",
                "placeholder": "e.g. 0 (EMIs only)"
            }),
            "active": forms.CheckboxInput(attrs={"class": "form-checkbox"}),
            "notes": forms.Textarea(attrs={
                "class": "form-textarea",
                "placeholder": "Optional details...",
                "rows": 3
            }),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields["category"].queryset = Category.objects.filter(user=user)

        # Remove blank choice '--------' and default initial values
        self.fields["type"].choices = RecurringItem.TypeChoices.choices
        self.fields["frequency"].choices = RecurringItem.FrequencyChoices.choices
        if not self.instance.pk:
            if not self.initial.get("type"):
                self.initial["type"] = RecurringItem.TypeChoices.SUBSCRIPTION
            if not self.initial.get("frequency"):
                self.initial["frequency"] = RecurringItem.FrequencyChoices.MONTHLY

    def clean_name(self):
        name = self.cleaned_data.get("name")
        if name:
            return StringProcessor(name).toTitle()
        return name

    def clean_notes(self):
        notes = self.cleaned_data.get("notes")
        if notes:
            return StringProcessor(notes).toCapitalize()
        return notes

    def clean_amount(self):
        amount = self.cleaned_data.get("amount")
        if amount is not None and amount <= 0:
            raise forms.ValidationError("Amount must be greater than zero.")
        return amount

    def clean(self):
        cleaned_data = super().clean()
        item_type = cleaned_data.get("type")
        total_inst = cleaned_data.get("total_installments")
        inst_paid = cleaned_data.get("installments_paid")
        end_date = cleaned_data.get("end_date")

        # Validation logic specific to EMI type
        if item_type == RecurringItem.TypeChoices.EMI:
            if total_inst is None:
                self.add_error("total_installments", "Total installments is required for EMIs.")
            if inst_paid is None:
                self.add_error("installments_paid", "Installments paid is required for EMIs.")
            if not end_date:
                self.add_error("end_date", "End date is required for EMIs.")
        return cleaned_data


class RecurringPaymentForm(forms.ModelForm):
    """
    Form for updating a specific recurring payment occurrence.
    """
    class Meta:
        model = RecurringPayment
        fields = ["recurring_item", "period_label", "due_date", "amount", "paid", "paid_date", "transaction"]
        widgets = {
            "recurring_item": forms.Select(attrs={"class": "form-select", "required": True}),
            "period_label": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": "e.g. 2026-07",
                "required": True
            }),
            "due_date": forms.DateInput(attrs={
                "class": "form-input",
                "type": "date",
                "required": True
            }),
            "amount": forms.TextInput(attrs={
                "class": "form-input indian-number",
                "placeholder": "0.00",
                "required": True
            }),
            "paid": forms.CheckboxInput(attrs={"class": "form-checkbox"}),
            "paid_date": forms.DateInput(attrs={
                "class": "form-input",
                "type": "date"
            }),
            "transaction": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields["recurring_item"].queryset = RecurringItem.objects.filter(user=user)
            self.fields["transaction"].queryset = Transaction.objects.filter(user=user)

    def clean_amount(self):
        amount = self.cleaned_data.get("amount")
        if amount is not None and amount <= 0:
            raise forms.ValidationError("Amount must be greater than zero.")
        return amount
