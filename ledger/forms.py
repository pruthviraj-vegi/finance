from django import forms
from decimal import Decimal
from django.db import models
from base.utility import StringProcessor
from ledger.models import Contact, Transaction, TransactionPayment
import re

class ContactForm(forms.ModelForm):
    """
    Form for creating and editing Contacts with validation and sanitization.
    """
    class Meta:
        model = Contact
        fields = ["name", "phone_number", "notes"]
        widgets = {
            "name": forms.TextInput(attrs={
                "class": "form-input", 
                "placeholder": "Enter contact name",
                "required": True
            }),
            "phone_number": forms.TextInput(attrs={
                "class": "form-input", 
                "placeholder": "Enter 10-digit phone number (e.g. 9876543210)",
                "type": "tel"
            }),
            "notes": forms.Textarea(attrs={
                "class": "form-textarea", 
                "placeholder": "Optional relationship, note, address...", 
                "rows": 3
            }),
        }

    def clean_name(self):
        name = self.cleaned_data.get("name")
        if name:
            return StringProcessor(name).toTitle()
        return name

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get("phone_number")
        if phone_number:
            # Normalize: strip spaces, dashes, parentheses
            phone_number = phone_number.strip().replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
            # Must be exactly 10 digits as required by model validator (phone_regex in base/manager.py)
            if not re.match(r"^\d{10}$", phone_number):
                raise forms.ValidationError("Phone number must be exactly 10 digits (e.g., 9876543210).")
        return phone_number


class TransactionForm(forms.ModelForm):
    """
    Form for creating and editing Transactions.
    """
    class Meta:
        model = Transaction
        fields = ["contact", "direction", "amount", "date", "reason", "due_date"]
        widgets = {
            "contact": forms.Select(attrs={"class": "form-select"}),
            "direction": forms.Select(attrs={"class": "form-select"}),
            "amount": forms.TextInput(attrs={
                "class": "form-input indian-number", 
                "placeholder": "0.00"
            }),
            "date": forms.DateInput(attrs={
                "class": "form-input", 
                "type": "date"
            }),
            "reason": forms.Textarea(attrs={
                "class": "form-textarea", 
                "placeholder": "Optional reason / description...", 
                "rows": 3
            }),
            "due_date": forms.DateInput(attrs={
                "class": "form-input", 
                "type": "date"
            }),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        if user:
            # Only show contacts belonging to the logged in user
            self.fields["contact"].queryset = Contact.objects.filter(user=user)

    def clean_amount(self):
        amount = self.cleaned_data.get("amount")
        if amount is not None and amount <= 0:
            raise forms.ValidationError("Amount must be greater than zero.")
        return amount


class TransactionPaymentForm(forms.ModelForm):
    """
    Form for creating and editing Transaction Payments (Repayments).
    """
    class Meta:
        model = TransactionPayment
        fields = ["transaction", "amount", "date", "note"]
        widgets = {
            "transaction": forms.Select(attrs={"class": "form-select"}),
            "amount": forms.TextInput(attrs={
                "class": "form-input indian-number", 
                "placeholder": "0.00"
            }),
            "date": forms.DateInput(attrs={
                "class": "form-input", 
                "type": "date"
            }),
            "note": forms.TextInput(attrs={
                "class": "form-input", 
                "placeholder": "Optional note (e.g. Cash, GPay, Bank transfer)..."
            }),
        }

    def __init__(self, *args, **kwargs):
        contact = kwargs.pop("contact", None)
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        
        if contact:
            # Show open or partially settled transactions for this contact
            self.fields["transaction"].queryset = Transaction.objects.filter(
                contact=contact,
                user=contact.user
            ).exclude(status=Transaction.StatusChoices.SETTLED)
        elif user:
            # Show open or partially settled transactions for this user
            self.fields["transaction"].queryset = Transaction.objects.filter(
                user=user
            ).exclude(status=Transaction.StatusChoices.SETTLED)

    def clean_amount(self):
        amount = self.cleaned_data.get("amount")
        if amount is not None and amount <= 0:
            raise forms.ValidationError("Amount must be greater than zero.")
        
        # Validate that the payment amount doesn't exceed the remaining balance
        transaction = self.cleaned_data.get("transaction")
        if transaction:
            # Calculate remaining balance
            total_repaid = transaction.payments.aggregate(total=models.Sum("amount"))["total"] or Decimal("0.00")
            
            # If editing, subtract current payment amount from total_repaid first
            if self.instance and self.instance.pk:
                total_repaid -= self.instance.amount

            remaining = transaction.amount - total_repaid
            if amount > remaining:
                raise forms.ValidationError(f"Amount exceeds the remaining balance of ₹{remaining:.2f}.")
                
        return amount


