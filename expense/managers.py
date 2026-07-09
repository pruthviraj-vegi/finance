from datetime import date
import calendar
from django.db import transaction
from django.utils import timezone
from expense.models import Transaction, RecurringPayment, RecurringItem


def add_months(sourcedate, months):
    """
    Utility function to add months to a python date object correctly.
    """
    month = sourcedate.month - 1 + months
    year = sourcedate.year + month // 12
    month = month % 12 + 1
    day = min(sourcedate.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def get_next_due_date(current_due, frequency):
    """
    Calculate the next due date based on the recurring frequency.
    """
    if frequency == "monthly":
        return add_months(current_due, 1)
    elif frequency == "quarterly":
        return add_months(current_due, 3)
    elif frequency == "yearly":
        return add_months(current_due, 12)
    return current_due


class RecurringPaymentManager:
    """
    Business logic for managing recurring payment occurrences.
    """

    @staticmethod
    @transaction.atomic
    def mark_as_paid(payment, paid_date=None):
        """
        Marks a recurring payment as paid.
        Creates a corresponding Transaction, links it, updates parent RecurringItem's
        next due date and installments.
        """
        if payment.paid:
            return payment

        if not paid_date:
            paid_date = timezone.localdate()

        # 1. Create a Transaction
        txn = Transaction.objects.create(
            user=payment.recurring_item.user,
            amount=payment.amount,
            type=Transaction.TypeChoices.EXPENSE,
            category=payment.recurring_item.category,
            date=paid_date,
            note=f"Paid {payment.recurring_item.name} for period {payment.period_label}",
            recurring_payment=payment
        )

        # 2. Update the Payment record
        payment.paid = True
        payment.paid_date = paid_date
        payment.transaction = txn
        payment.save()

        # 3. Update the RecurringItem
        item = payment.recurring_item
        if item.type == RecurringItem.TypeChoices.EMI:
            if item.installments_paid is None:
                item.installments_paid = 0
            item.installments_paid += 1
            # If all installments are paid, we can deactivate it
            if item.total_installments and item.installments_paid >= item.total_installments:
                item.active = False

        # Calculate next due date
        item.next_due_date = get_next_due_date(item.next_due_date, item.frequency)
        item.save()

        # 4. Generate the NEXT RecurringPayment slot if the item is still active
        if item.active:
            next_due = item.next_due_date
            if item.frequency == "monthly":
                next_label = next_due.strftime("%Y-%m")
            elif item.frequency == "quarterly":
                q = (next_due.month - 1) // 3 + 1
                next_label = f"{next_due.year}-Q{q}"
            else:
                next_label = f"{next_due.year}"

            # Create next unpaid recurring payment slot if not already exists
            RecurringPayment.objects.get_or_create(
                recurring_item=item,
                period_label=next_label,
                defaults={
                    "due_date": next_due,
                    "amount": item.amount,
                    "paid": False
                }
            )

        return payment

    @staticmethod
    @transaction.atomic
    def mark_as_unpaid(payment):
        """
        Reverts a paid recurring payment to unpaid status.
        Deletes the linked Transaction, updates the parent RecurringItem's due dates and installments.
        """
        if not payment.paid:
            return payment

        # 1. Delete/unlink the transaction
        txn = payment.transaction
        if txn:
            payment.transaction = None
            payment.save()
            txn.delete()

        # 2. Update Payment record
        payment.paid = False
        payment.paid_date = None
        payment.save()

        # 3. Revert parent RecurringItem
        item = payment.recurring_item
        if item.type == RecurringItem.TypeChoices.EMI:
            if item.installments_paid and item.installments_paid > 0:
                item.installments_paid -= 1
            # Reactivate if it was completed
            if not item.active and (item.total_installments is None or (item.installments_paid or 0) < item.total_installments):
                item.active = True

        # Revert next due date to the current payment's due date
        item.next_due_date = payment.due_date
        item.save()

        # Delete any future unpaid recurring payments generated
        RecurringPayment.objects.filter(
            recurring_item=item,
            paid=False,
            due_date__gt=payment.due_date
        ).delete()

        return payment
