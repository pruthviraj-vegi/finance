from decimal import Decimal
from django.db import models
from django.conf import settings
from base.manager import SoftDeleteModel
from base.utility import StringProcessor


class Contact(SoftDeleteModel):
    """
    Model representing a contact for lending/borrowing (friend/family/etc).
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="contacts",
        verbose_name="User",
    )
    name = models.CharField(max_length=255, verbose_name="Name")
    phone_number = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        verbose_name="Phone Number",
    )
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name="Notes",
        help_text="Optional, e.g. relationship",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    def save(self, *args, **kwargs):
        self.name = StringProcessor(self.name).toTitle()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name}"

    @property
    def net_balance(self):
        """
        Calculates the net balance for this contact.
        Positive: they owe you (given / green).
        Negative: you owe them (taken / red).
        """
        from django.db.models import Sum, Case, When, Value, DecimalField
        
        # Aggregate transactions in a single query
        txn_stats = self.transactions.aggregate(
            lent=Sum(Case(When(direction="given", then="amount"), default=Value(0), output_field=DecimalField())),
            borrowed=Sum(Case(When(direction="taken", then="amount"), default=Value(0), output_field=DecimalField()))
        )
        total_lent = txn_stats["lent"] or Decimal("0.00")
        total_borrowed = txn_stats["borrowed"] or Decimal("0.00")
        
        # Aggregate payments in a single query
        pm_stats = TransactionPayment.objects.filter(transaction__contact=self).aggregate(
            received=Sum(Case(When(transaction__direction="given", then="amount"), default=Value(0), output_field=DecimalField())),
            made=Sum(Case(When(transaction__direction="taken", then="amount"), default=Value(0), output_field=DecimalField()))
        )
        payments_received = pm_stats["received"] or Decimal("0.00")
        payments_made = pm_stats["made"] or Decimal("0.00")
        
        return (total_lent - payments_received) - (total_borrowed - payments_made)

    @property
    def net_balance_abs(self):
        return abs(self.net_balance)

    class Meta:
        verbose_name = "Contact"
        verbose_name_plural = "Contacts"
        ordering = ["name"]


class Transaction(SoftDeleteModel):
    """
    Model representing a transaction (money given to or taken from a contact).
    """

    class DirectionChoices(models.TextChoices):
        GIVEN = "given", "Given"
        TAKEN = "taken", "Taken"

    class StatusChoices(models.TextChoices):
        OPEN = "open", "Open"
        PARTIALLY_SETTLED = "partially_settled", "Partially Settled"
        SETTLED = "settled", "Settled"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="transactions",
        verbose_name="User",
    )
    contact = models.ForeignKey(
        Contact,
        on_delete=models.CASCADE,
        related_name="transactions",
        verbose_name="Contact",
    )
    direction = models.CharField(
        max_length=10,
        choices=DirectionChoices.choices,
        verbose_name="Direction",
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Amount",
    )
    date = models.DateField(verbose_name="Date")
    reason = models.TextField(
        blank=True,
        null=True,
        verbose_name="Reason",
        help_text="Optional note, e.g. 'for bike repair'",
    )
    due_date = models.DateField(
        blank=True,
        null=True,
        verbose_name="Due Date",
        help_text="Optional expected return date",
    )
    status = models.CharField(
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.OPEN,
        verbose_name="Status",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    def update_status(self):
        """
        Recalculates and updates the status of the transaction based on its active payments.
        """
        total_repaid = self.payments.aggregate(total=models.Sum("amount"))[
            "total"
        ] or Decimal("0.00")

        if total_repaid <= 0:
            new_status = self.StatusChoices.OPEN
        elif total_repaid < self.amount:
            new_status = self.StatusChoices.PARTIALLY_SETTLED
        else:
            new_status = self.StatusChoices.SETTLED

        if self.status != new_status:
            self.status = new_status
            self.save(update_fields=["status"])

    def save(self, *args, **kwargs):
        # Automatically update status based on existing active payments on save,
        # but skip this if we are only saving the status field to prevent recursion.
        update_fields = kwargs.get("update_fields")
        if not update_fields or "status" not in update_fields:
            if self.pk:
                total_repaid = self.payments.aggregate(total=models.Sum("amount"))[
                    "total"
                ] or Decimal("0.00")

                if total_repaid <= 0:
                    self.status = self.StatusChoices.OPEN
                elif total_repaid < self.amount:
                    self.status = self.StatusChoices.PARTIALLY_SETTLED
                else:
                    self.status = self.StatusChoices.SETTLED

        super().save(*args, **kwargs)

    def __str__(self):
        direction_label = (
            "Lent to"
            if self.direction == self.DirectionChoices.GIVEN
            else "Borrowed from"
        )
        return f"{self.amount} {direction_label} {self.contact.name} on {self.date}"

    class Meta:
        verbose_name = "Transaction"
        verbose_name_plural = "Transactions"
        ordering = ["-date", "-created_at"]


class TransactionPayment(SoftDeleteModel):
    """
    Model representing a payment event against a transaction (loan).
    """

    transaction = models.ForeignKey(
        Transaction,
        on_delete=models.CASCADE,
        related_name="payments",
        verbose_name="Transaction",
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Amount",
    )
    date = models.DateField(verbose_name="Date")
    note = models.TextField(
        blank=True,
        null=True,
        verbose_name="Note",
        help_text="e.g. 'paid back half in cash'",
    )
    linked_transaction = models.ForeignKey(
        Transaction,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="linked_payments",
        verbose_name="Linked Transaction",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.transaction.update_status()

    def __str__(self):
        return f"Payment of {self.amount} for Transaction {self.transaction_id} on {self.date}"

    class Meta:
        verbose_name = "Transaction Payment"
        verbose_name_plural = "Transaction Payments"
        ordering = ["-date", "-created_at"]
