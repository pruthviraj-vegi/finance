from django.views.generic import CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Q
from django.shortcuts import render
from django.http import HttpResponseRedirect
from decimal import Decimal
from django.db import models
from django.utils import timezone

from base.decorators import required_permission, RequiredPermissionMixin
from base.utility import render_paginated_response, table_sorting
from ledger.models import Contact, Transaction, TransactionPayment
from ledger.forms import ContactForm, TransactionForm, TransactionPaymentForm

# ============================================
# CONTACT LISTING (Home/Fetch Split Pattern)
# ============================================

@required_permission("ledger.view_contact")
def contact_home(request):
    """
    Renders the empty shell template for the contacts list.
    No queryset is loaded on initial paint.
    """
    context = {
        "active_page": "contacts",
    }
    return render(request, "ledger/contact_list.html", context)


def contact_get_data(request):
    """
    Helper function to filter, search, and sort contacts for the current user.
    """
    search_query = request.GET.get("search", "").strip()
    
    # Base queryset for current user (excludes soft-deleted items automatically via manager)
    queryset = Contact.objects.filter(user=request.user)
    
    # Filter by search terms
    if search_query:
        words = search_query.split()
        q_filters = Q()
        for word in words:
            q_filters &= (
                Q(name__icontains=word) |
                Q(phone_number__icontains=word) |
                Q(notes__icontains=word)
            )
        queryset = queryset.filter(q_filters)
        
    # Multi-column sorting helper
    valid_sorts = ["name", "phone_number", "created_at"]
    sort_fields = table_sorting(request, valid_sorts, default_sort="name")
    
    return queryset.order_by(*sort_fields)


@required_permission("ledger.view_contact")
def fetch_contacts(request):
    """
    AJAX endpoint to fetch contact list page rows, paginated and sorted.
    """
    contacts = contact_get_data(request)
    current_sort = request.GET.get("sort", "name")
    return render_paginated_response(
        request=request,
        queryset=contacts,
        table_template="ledger/partials/contact_fetch.html",
        per_page=10,
        current_sort=current_sort
    )


# ============================================
# CONTACT WRITE OPERATIONS (CBVs)
# ============================================

class ContactCreateView(RequiredPermissionMixin, CreateView):
    """
    View to create a new contact.
    """
    model = Contact
    form_class = ContactForm
    template_name = "ledger/contact_form.html"
    success_url = reverse_lazy("ledger:contact_list")
    required_permission = "ledger.add_contact"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["active_page"] = "contacts"
        context["is_create"] = True
        return context

    def form_valid(self, form):
        # Bind the contact to the currently logged in user
        form.instance.user = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, f"Contact '{self.object.name}' has been created successfully.")
        return response


class ContactUpdateView(RequiredPermissionMixin, UpdateView):
    """
    View to edit an existing contact.
    """
    model = Contact
    form_class = ContactForm
    template_name = "ledger/contact_form.html"
    success_url = reverse_lazy("ledger:contact_list")
    required_permission = "ledger.change_contact"

    def get_queryset(self):
        # Limit access to own contacts
        return Contact.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["active_page"] = "contacts"
        context["is_create"] = False
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"Contact '{self.object.name}' has been updated successfully.")
        return response


class ContactDeleteView(RequiredPermissionMixin, DeleteView):
    """
    View to delete a contact (soft delete).
    """
    model = Contact
    template_name = "ledger/contact_confirm_delete.html"
    success_url = reverse_lazy("ledger:contact_list")
    required_permission = "ledger.delete_contact"

    def get_queryset(self):
        # Limit access to own contacts
        return Contact.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["active_page"] = "contacts"
        return context

    def form_valid(self, form):
        success_url = self.get_success_url()
        contact_name = self.object.name
        # Soft delete is triggered automatically by model's delete() method
        self.object.delete()
        messages.success(self.request, f"Contact '{contact_name}' has been deleted successfully.")
        return HttpResponseRedirect(success_url)


# ============================================
# TRANSACTION LISTING (Home/Fetch Split Pattern)
# ============================================

@required_permission("ledger.view_transaction")
def transaction_home(request):
    """
    Renders the empty shell template for the transactions list.
    No queryset is loaded on initial paint.
    """
    # Fetch contacts to populate the contact filter dropdown
    contacts = Contact.objects.filter(user=request.user)
    context = {
        "active_page": "transactions",
        "contacts": contacts,
        "directions": Transaction.DirectionChoices.choices,
        "statuses": Transaction.StatusChoices.choices,
    }
    return render(request, "ledger/transaction_list.html", context)


def transaction_get_data(request):
    """
    Helper function to filter, search, and sort transactions for the current user.
    """
    search_query = request.GET.get("search", "").strip()
    direction_filter = request.GET.get("direction", "").strip()
    status_filter = request.GET.get("status", "").strip()
    contact_filter = request.GET.get("contact", "").strip()
    
    # Base queryset for current user (excludes soft-deleted items automatically via manager)
    queryset = Transaction.objects.filter(user=request.user).select_related("contact")
    
    # Filter by direction
    if direction_filter:
        queryset = queryset.filter(direction=direction_filter)
        
    # Filter by status
    if status_filter:
        queryset = queryset.filter(status=status_filter)

    # Filter by contact
    if contact_filter:
        queryset = queryset.filter(contact_id=contact_filter)
        
    # Filter by search terms
    if search_query:
        words = search_query.split()
        q_filters = Q()
        for word in words:
            q_filters &= (
                Q(contact__name__icontains=word) |
                Q(reason__icontains=word) |
                Q(amount__icontains=word)
            )
        queryset = queryset.filter(q_filters)
        
    # Multi-column sorting helper
    valid_sorts = {
        "contact": "contact__name",
        "direction": "direction",
        "amount": "amount",
        "date": "date",
        "status": "status",
        "created_at": "created_at"
    }
    sort_fields = table_sorting(request, valid_sorts, default_sort="-date")
    
    return queryset.order_by(*sort_fields)


@required_permission("ledger.view_transaction")
def fetch_transactions(request):
    """
    AJAX endpoint to fetch transaction list page rows, paginated and sorted.
    """
    transactions = transaction_get_data(request)
    current_sort = request.GET.get("sort", "-date")
    return render_paginated_response(
        request=request,
        queryset=transactions,
        table_template="ledger/partials/transaction_fetch.html",
        per_page=10,
        current_sort=current_sort
    )


# ============================================
# TRANSACTION WRITE OPERATIONS (CBVs)
# ============================================

class TransactionCreateView(RequiredPermissionMixin, CreateView):
    """
    View to create a new transaction.
    """
    model = Transaction
    form_class = TransactionForm
    template_name = "ledger/transaction_form.html"
    success_url = reverse_lazy("ledger:transaction_list")
    required_permission = "ledger.add_transaction"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        initial["date"] = timezone.localdate()
        contact_id = self.request.GET.get("contact")
        if contact_id:
            initial["contact"] = contact_id
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["active_page"] = "transactions"
        context["is_create"] = True
        context["next_url"] = self.request.GET.get("next") or self.request.POST.get("next") or ""
        return context

    def form_valid(self, form):
        form.instance.user = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, f"Transaction for {self.object.amount} has been recorded successfully.")
        return response

    def get_success_url(self):
        next_url = self.request.POST.get("next")
        if next_url:
            return next_url
        return self.success_url


class TransactionUpdateView(RequiredPermissionMixin, UpdateView):
    """
    View to edit an existing transaction.
    """
    model = Transaction
    form_class = TransactionForm
    template_name = "ledger/transaction_form.html"
    success_url = reverse_lazy("ledger:transaction_list")
    required_permission = "ledger.change_transaction"

    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["active_page"] = "transactions"
        context["is_create"] = False
        context["next_url"] = self.request.GET.get("next") or self.request.POST.get("next") or ""
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Transaction has been updated successfully.")
        return response

    def get_success_url(self):
        next_url = self.request.POST.get("next")
        if next_url:
            return next_url
        return self.success_url


class TransactionDeleteView(RequiredPermissionMixin, DeleteView):
    """
    View to delete a transaction (soft delete).
    """
    model = Transaction
    template_name = "ledger/transaction_confirm_delete.html"
    success_url = reverse_lazy("ledger:transaction_list")
    required_permission = "ledger.delete_transaction"

    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["active_page"] = "transactions"
        context["next_url"] = self.request.GET.get("next") or self.request.POST.get("next") or ""
        return context

    def form_valid(self, form):
        success_url = self.get_success_url()
        self.object.delete()
        messages.success(self.request, "Transaction has been deleted successfully.")
        return HttpResponseRedirect(success_url)

    def get_success_url(self):
        next_url = self.request.POST.get("next")
        if next_url:
            return next_url
        return self.success_url


# ============================================
# CONTACT DETAIL & REPAYMENTS (Unified Interface)
# ============================================

class ContactDetailView(RequiredPermissionMixin, DetailView):
    """
    View to display the details of a contact, including their transactions, repayments,
    and inline forms to record new ones.
    """
    model = Contact
    template_name = "ledger/contact_detail.html"
    context_object_name = "contact"
    required_permission = "ledger.view_contact"

    def get_queryset(self):
        return Contact.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["active_page"] = "contacts"
        
        # Get all transactions for this contact
        transactions = self.object.transactions.all().order_by("-date", "-created_at")
        context["transactions"] = transactions

        # Build unified chronological ledger entries
        ledger_entries = []
        for txn in transactions:
            ledger_entries.append({
                "type": "transaction",
                "pk": txn.pk,
                "date": txn.date,
                "created_at": txn.created_at,
                "direction": txn.direction,
                "amount": txn.amount,
                "label": "Lent (Given)" if txn.direction == Transaction.DirectionChoices.GIVEN else "Borrowed (Taken)",
                "note": txn.reason,
                "status": txn.status,
            })
            for pm in txn.payments.all():
                is_received = (txn.direction == Transaction.DirectionChoices.GIVEN)
                ledger_entries.append({
                    "type": "payment",
                    "pk": pm.pk,
                    "date": pm.date,
                    "created_at": pm.created_at,
                    "direction": "received" if is_received else "paid",
                    "amount": pm.amount,
                    "label": "Repayment received" if is_received else "Repayment paid",
                    "note": pm.note,
                    "status": "settled",
                })

        # Sort ledger entries by date descending, then created_at descending
        ledger_entries.sort(key=lambda x: (x["date"], x["created_at"]), reverse=True)
        context["ledger_entries"] = ledger_entries
        
        # Calculate summary stats
        total_lent = transactions.filter(direction=Transaction.DirectionChoices.GIVEN).aggregate(
            total=models.Sum("amount")
        )["total"] or Decimal("0.00")
        
        total_borrowed = transactions.filter(direction=Transaction.DirectionChoices.TAKEN).aggregate(
            total=models.Sum("amount")
        )["total"] or Decimal("0.00")
        
        payments_received = TransactionPayment.objects.filter(
            transaction__contact=self.object,
            transaction__direction=Transaction.DirectionChoices.GIVEN
        ).aggregate(total=models.Sum("amount"))["total"] or Decimal("0.00")
        
        payments_made = TransactionPayment.objects.filter(
            transaction__contact=self.object,
            transaction__direction=Transaction.DirectionChoices.TAKEN
        ).aggregate(total=models.Sum("amount"))["total"] or Decimal("0.00")
        
        net_balance = (total_lent - payments_received) - (total_borrowed - payments_made)
        
        context["total_lent"] = total_lent
        context["total_borrowed"] = total_borrowed
        context["payments_received"] = payments_received
        context["payments_made"] = payments_made
        context["net_balance"] = net_balance
        context["net_balance_abs"] = abs(net_balance)
        
        # Inline transaction form (prefilled with this contact & today's date)
        from django.utils import timezone
        context["transaction_form"] = TransactionForm(
            user=self.request.user,
            initial={"contact": self.object, "date": timezone.localdate()}
        )
        
        # Inline repayment form (prefilled with open transactions of this contact & today's date)
        context["payment_form"] = TransactionPaymentForm(
            contact=self.object,
            initial={"date": timezone.localdate()}
        )
        
        return context


class TransactionPaymentCreateView(RequiredPermissionMixin, CreateView):
    """
    View to record a repayment (payment against a transaction).
    """
    model = TransactionPayment
    form_class = TransactionPaymentForm
    template_name = "ledger/payment_form.html"
    required_permission = "ledger.add_transactionpayment"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        contact_id = self.request.GET.get("contact")
        if contact_id:
            try:
                kwargs["contact"] = Contact.objects.get(pk=contact_id, user=self.request.user)
            except Contact.DoesNotExist:
                pass
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        initial["date"] = timezone.localdate()
        transaction_id = self.request.GET.get("transaction")
        if transaction_id:
            initial["transaction"] = transaction_id
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["next_url"] = self.request.GET.get("next") or self.request.POST.get("next") or ""
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        transaction = form.instance.transaction
        messages.success(
            self.request, 
            f"Repayment of ₹{form.instance.amount} recorded for transaction: {transaction}"
        )
        return response

    def get_success_url(self):
        next_url = self.request.POST.get("next")
        if next_url:
            return next_url
        transaction = self.object.transaction
        return reverse_lazy("ledger:contact_detail", kwargs={"pk": transaction.contact.pk})


class TransactionPaymentUpdateView(RequiredPermissionMixin, UpdateView):
    """
    View to edit an existing repayment.
    """
    model = TransactionPayment
    form_class = TransactionPaymentForm
    template_name = "ledger/payment_form.html"
    required_permission = "ledger.change_transactionpayment"

    def get_queryset(self):
        return TransactionPayment.objects.filter(transaction__user=self.request.user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        if self.object:
            kwargs["contact"] = self.object.transaction.contact
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["active_page"] = "contacts"
        context["next_url"] = self.request.GET.get("next") or self.request.POST.get("next") or ""
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Repayment has been updated successfully.")
        return response

    def get_success_url(self):
        next_url = self.request.POST.get("next")
        if next_url:
            return next_url
        return reverse_lazy("ledger:contact_detail", kwargs={"pk": self.object.transaction.contact.pk})


class TransactionPaymentDeleteView(RequiredPermissionMixin, DeleteView):
    """
    View to delete a repayment.
    """
    model = TransactionPayment
    required_permission = "ledger.delete_transactionpayment"

    def get_queryset(self):
        return TransactionPayment.objects.filter(transaction__user=self.request.user)

    def form_valid(self, form):
        success_url = self.get_success_url()
        payment_amount = self.object.amount
        self.object.delete()
        messages.success(self.request, f"Repayment of ₹{payment_amount} has been deleted successfully.")
        return HttpResponseRedirect(success_url)

    def get_success_url(self):
        next_url = self.request.POST.get("next")
        if next_url:
            return next_url
        return reverse_lazy("ledger:contact_detail", kwargs={"pk": self.object.transaction.contact.pk})


