from django.db import models
from django.conf import settings
from base.manager import SoftDeleteModel
from base.utility import StringProcessor


class Category(SoftDeleteModel):
    """
    Model representing a category for transactions (e.g. Food, Rent, Entertainment).
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="categories",
        verbose_name="User",
    )
    name = models.CharField(max_length=255, verbose_name="Name")
    color = models.CharField(
        max_length=50,
        default="#cbd5e1",
        verbose_name="Color",
        help_text="For consistent chart coloring",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    def save(self, *args, **kwargs):
        self.name = StringProcessor(self.name).toTitle()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        ordering = ["name"]


class Transaction(SoftDeleteModel):
    """
    Model representing an expense or income transaction.
    """

    class TypeChoices(models.TextChoices):
        INCOME = "income", "Income"
        EXPENSE = "expense", "Expense"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="expense_transactions",
        verbose_name="User",
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Amount",
    )
    type = models.CharField(
        max_length=10,
        choices=TypeChoices.choices,
        verbose_name="Type",
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="transactions",
        verbose_name="Category",
    )
    date = models.DateField(verbose_name="Date")
    note = models.TextField(
        blank=True,
        null=True,
        verbose_name="Note",
    )
    recurring_payment = models.ForeignKey(
        "RecurringPayment",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="transactions",
        verbose_name="Recurring Payment",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    def save(self, *args, **kwargs):
        if self.note:
            self.note = StringProcessor(self.note).toCapitalize()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.type.capitalize()} of {self.amount} on {self.date}"

    class Meta:
        verbose_name = "Transaction"
        verbose_name_plural = "Transactions"
        ordering = ["-date", "-created_at"]


class RecurringItem(SoftDeleteModel):
    """
    Model representing a recurring obligation (EMI, subscription, or renewal).
    """

    class TypeChoices(models.TextChoices):
        EMI = "emi", "EMI"
        SUBSCRIPTION = "subscription", "Subscription"
        RENEWAL = "renewal", "Renewal"

    class FrequencyChoices(models.TextChoices):
        MONTHLY = "monthly", "Monthly"
        QUARTERLY = "quarterly", "Quarterly"
        YEARLY = "yearly", "Yearly"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="recurring_items",
        verbose_name="User",
    )
    name = models.CharField(max_length=255, verbose_name="Name")
    type = models.CharField(
        max_length=20,
        choices=TypeChoices.choices,
        verbose_name="Type",
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="recurring_items",
        verbose_name="Category",
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Amount",
    )
    frequency = models.CharField(
        max_length=20,
        choices=FrequencyChoices.choices,
        verbose_name="Frequency",
    )
    start_date = models.DateField(verbose_name="Start Date")
    end_date = models.DateField(
        blank=True,
        null=True,
        verbose_name="End Date",
        help_text="NULL if indefinite (most subscriptions), set for EMIs with fixed tenure",
    )
    next_due_date = models.DateField(verbose_name="Next Due Date")
    total_installments = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Total Installments",
        help_text="NULL for subscriptions/renewals, set for EMIs",
    )
    installments_paid = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Installments Paid",
        help_text="NULL for subscriptions/renewals, tracked for EMIs",
    )
    active = models.BooleanField(
        default=True,
        verbose_name="Active",
        help_text="Allows canceling something without deleting its history",
    )
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name="Notes",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    def save(self, *args, **kwargs):
        self.name = StringProcessor(self.name).toTitle()
        if self.notes:
            self.notes = StringProcessor(self.notes).toCapitalize()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.type.capitalize()})"

    class Meta:
        verbose_name = "Recurring Item"
        verbose_name_plural = "Recurring Items"
        ordering = ["next_due_date", "name"]


class RecurringPayment(SoftDeleteModel):
    """
    Model representing one due cycle / instance of a recurring item.
    """

    recurring_item = models.ForeignKey(
        RecurringItem,
        on_delete=models.CASCADE,
        related_name="payments",
        verbose_name="Recurring Item",
    )
    period_label = models.CharField(
        max_length=50,
        verbose_name="Period Label",
        help_text="e.g. '2026-07' for monthly, '2026' for yearly",
    )
    due_date = models.DateField(verbose_name="Due Date")
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Amount",
        help_text="Usually matches recurring_items.amount, but allows for fee hikes/late fees",
    )
    paid = models.BooleanField(default=False, verbose_name="Paid")
    paid_date = models.DateField(
        blank=True,
        null=True,
        verbose_name="Paid Date",
    )
    transaction = models.ForeignKey(
        Transaction,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="recurring_payments",
        verbose_name="Transaction",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.recurring_item.name} - {self.period_label} ({'Paid' if self.paid else 'Unpaid'})"

    class Meta:
        verbose_name = "Recurring Payment"
        verbose_name_plural = "Recurring Payments"
        ordering = ["due_date"]
