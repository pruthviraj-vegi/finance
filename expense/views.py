from django.views.generic import CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Q
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseRedirect
from django.utils import timezone

from base.decorators import required_permission, RequiredPermissionMixin
from base.utility import render_paginated_response, table_sorting
from expense.models import Category, Transaction, RecurringItem, RecurringPayment
from expense.forms import CategoryForm, TransactionForm, RecurringItemForm, RecurringPaymentForm
from expense.managers import RecurringPaymentManager


# ============================================
# CATEGORY LISTING (Home/Fetch Split Pattern)
# ============================================

@required_permission("expense.view_category")
def category_home(request):
    """
    Renders the empty shell template for the categories list.
    No queryset is loaded on initial paint.
    """
    context = {
        "active_page": "categories",
    }
    return render(request, "expense/category_list.html", context)


def category_get_data(request):
    """
    Helper function to filter, search, and sort categories for the current user.
    """
    search_query = request.GET.get("search", "").strip()
    queryset = Category.objects.filter(user=request.user)

    if search_query:
        queryset = queryset.filter(name__icontains=search_query)

    valid_sorts = ["name", "created_at"]
    sort_fields = table_sorting(request, valid_sorts, default_sort="name")

    return queryset.order_by(*sort_fields)


@required_permission("expense.view_category")
def fetch_categories(request):
    """
    AJAX endpoint to fetch category list page rows, paginated and sorted.
    """
    categories = category_get_data(request)
    current_sort = request.GET.get("sort", "name")
    return render_paginated_response(
        request=request,
        queryset=categories,
        table_template="expense/partials/category_fetch.html",
        per_page=10,
        current_sort=current_sort
    )


# ============================================
# CATEGORY WRITE OPERATIONS (CBVs)
# ============================================

class CategoryCreateView(RequiredPermissionMixin, CreateView):
    """
    View to create a new category.
    """
    model = Category
    form_class = CategoryForm
    template_name = "expense/category_form.html"
    success_url = reverse_lazy("expense:category_list")
    required_permission = "expense.add_category"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["active_page"] = "categories"
        context["is_create"] = True
        return context

    def form_valid(self, form):
        form.instance.user = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, f"Category '{self.object.name}' has been created successfully.")
        return response


class CategoryUpdateView(RequiredPermissionMixin, UpdateView):
    """
    View to edit an existing category.
    """
    model = Category
    form_class = CategoryForm
    template_name = "expense/category_form.html"
    success_url = reverse_lazy("expense:category_list")
    required_permission = "expense.change_category"

    def get_queryset(self):
        return Category.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["active_page"] = "categories"
        context["is_create"] = False
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"Category '{self.object.name}' has been updated successfully.")
        return response


class CategoryDeleteView(RequiredPermissionMixin, DeleteView):
    """
    View to delete a category (soft delete).
    """
    model = Category
    template_name = "expense/category_confirm_delete.html"
    success_url = reverse_lazy("expense:category_list")
    required_permission = "expense.delete_category"

    def get_queryset(self):
        return Category.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["active_page"] = "categories"
        return context

    def form_valid(self, form):
        success_url = self.get_success_url()
        category_name = self.object.name
        self.object.delete()
        messages.success(self.request, f"Category '{category_name}' has been deleted successfully.")
        return HttpResponseRedirect(success_url)


# ============================================
# TRANSACTION LISTING (Home/Fetch Split Pattern)
# ============================================

@required_permission("expense.view_transaction")
def transaction_home(request):
    """
    Renders the empty shell template for the transactions list.
    No queryset is loaded on initial paint.
    """
    categories = Category.objects.filter(user=request.user)
    context = {
        "active_page": "transactions",
        "categories": categories,
        "types": Transaction.TypeChoices.choices,
    }
    return render(request, "expense/transaction_list.html", context)


def transaction_get_data(request):
    """
    Helper function to filter, search, and sort transactions for the current user.
    """
    search_query = request.GET.get("search", "").strip()
    type_filter = request.GET.get("type", "").strip()
    category_filter = request.GET.get("category", "").strip()

    queryset = Transaction.objects.filter(user=request.user).select_related("category")

    if type_filter:
        queryset = queryset.filter(type=type_filter)

    if category_filter:
        queryset = queryset.filter(category_id=category_filter)

    if search_query:
        words = search_query.split()
        q_filters = Q()
        for word in words:
            q_filters &= (
                Q(category__name__icontains=word) |
                Q(note__icontains=word) |
                Q(amount__icontains=word)
            )
        queryset = queryset.filter(q_filters)

    valid_sorts = {
        "category": "category__name",
        "type": "type",
        "amount": "amount",
        "date": "date",
        "created_at": "created_at"
    }
    sort_fields = table_sorting(request, valid_sorts, default_sort="-date")

    return queryset.order_by(*sort_fields)


@required_permission("expense.view_transaction")
def fetch_transactions(request):
    """
    AJAX endpoint to fetch transaction list page rows, paginated and sorted.
    """
    transactions = transaction_get_data(request)
    current_sort = request.GET.get("sort", "-date")
    return render_paginated_response(
        request=request,
        queryset=transactions,
        table_template="expense/partials/transaction_fetch.html",
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
    template_name = "expense/transaction_form.html"
    success_url = reverse_lazy("expense:transaction_list")
    required_permission = "expense.add_transaction"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        initial["date"] = timezone.localdate()
        category_id = self.request.GET.get("category")
        if category_id:
            initial["category"] = category_id
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
    template_name = "expense/transaction_form.html"
    success_url = reverse_lazy("expense:transaction_list")
    required_permission = "expense.change_transaction"

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
    template_name = "expense/transaction_confirm_delete.html"
    success_url = reverse_lazy("expense:transaction_list")
    required_permission = "expense.delete_transaction"

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
# RECURRING DASHBOARD & LISTING (Home/Fetch Split Pattern)
# ============================================

@required_permission("expense.view_recurringitem")
def recurring_dashboard(request):
    """
    Renders a card-based dashboard for recurring items,
    inspired by the Vault Glass Stitch design.
    Each active item is shown as a card with its pending payment status.
    """
    from django.db.models import Sum, Prefetch
    from datetime import timedelta
    from decimal import Decimal
    import calendar

    today = timezone.localdate()

    # Prefetch each item's next unpaid payment for inline display
    pending_payments_prefetch = Prefetch(
        "payments",
        queryset=RecurringPayment.objects.filter(paid=False).order_by("due_date"),
        to_attr="pending_payments"
    )
    active_items = (
        RecurringItem.objects.filter(user=request.user, active=True)
        .select_related("category")
        .prefetch_related(pending_payments_prefetch)
        .order_by("next_due_date")
    )

    total_active = active_items.count()

    # Calculate approximate monthly commitment (only for monthly items)
    monthly_commitment = sum(
        (item.amount for item in active_items if item.frequency == "monthly"),
        Decimal("0.00")
    )

    # Count of active items only among those with monthly frequency for the breakdown bar
    monthly_active_items = [i for i in active_items if i.frequency == "monthly"]
    monthly_emis = sum(1 for i in monthly_active_items if i.type == "emi")
    monthly_subscriptions = sum(1 for i in monthly_active_items if i.type == "subscription")
    monthly_renewals = sum(1 for i in monthly_active_items if i.type == "renewal")

    # Calculate actual due this month (calendar month)
    start_of_month = today.replace(day=1)
    _, last_day = calendar.monthrange(today.year, today.month)
    end_of_month = today.replace(day=last_day)

    this_month_payments = RecurringPayment.objects.filter(
        recurring_item__user=request.user,
        recurring_item__active=True,
        due_date__gte=start_of_month,
        due_date__lte=end_of_month
    )
    this_month_total = sum((p.amount for p in this_month_payments), Decimal("0.00"))
    this_month_paid = sum((p.amount for p in this_month_payments if p.paid), Decimal("0.00"))
    this_month_unpaid = sum((p.amount for p in this_month_payments if not p.paid), Decimal("0.00"))

    # Overdue count/sum (payments past due date that are unpaid)
    overdue_qs = RecurringPayment.objects.filter(
        recurring_item__user=request.user,
        paid=False,
        due_date__lt=today
    )
    overdue_count = overdue_qs.count()
    overdue_sum = overdue_qs.aggregate(total=Sum("amount"))["total"] or 0

    context = {
        "active_page": "recurring_dashboard",
        "active_items": active_items,
        "total_active": total_active,
        "monthly_emis": monthly_emis,
        "monthly_subscriptions": monthly_subscriptions,
        "monthly_renewals": monthly_renewals,
        "monthly_commitment": monthly_commitment,
        "this_month_total": this_month_total,
        "this_month_paid": this_month_paid,
        "this_month_unpaid": this_month_unpaid,
        "overdue_count": overdue_count,
        "overdue_sum": overdue_sum,
        "today": today,
    }
    return render(request, "expense/recurring_dashboard.html", context)


@required_permission("expense.view_recurringitem")
def recurring_item_home(request):
    """
    Renders the empty shell template for the recurring items list.
    No queryset is loaded on initial paint.
    """
    categories = Category.objects.filter(user=request.user)
    context = {
        "active_page": "recurring",
        "categories": categories,
        "types": RecurringItem.TypeChoices.choices,
        "frequencies": RecurringItem.FrequencyChoices.choices,
    }
    return render(request, "expense/recurring_item_list.html", context)


def recurring_item_get_data(request):
    """
    Helper function to filter, search, and sort recurring items for the current user.
    """
    search_query = request.GET.get("search", "").strip()
    type_filter = request.GET.get("type", "").strip()
    category_filter = request.GET.get("category", "").strip()

    queryset = RecurringItem.objects.filter(user=request.user).select_related("category")

    if type_filter:
        queryset = queryset.filter(type=type_filter)

    if category_filter:
        queryset = queryset.filter(category_id=category_filter)

    if search_query:
        words = search_query.split()
        q_filters = Q()
        for word in words:
            q_filters &= (
                Q(name__icontains=word) |
                Q(category__name__icontains=word) |
                Q(amount__icontains=word)
            )
        queryset = queryset.filter(q_filters)

    valid_sorts = {
        "name": "name",
        "type": "type",
        "category": "category__name",
        "amount": "amount",
        "next_due_date": "next_due_date",
        "created_at": "created_at"
    }
    sort_fields = table_sorting(request, valid_sorts, default_sort="next_due_date")

    return queryset.order_by(*sort_fields)


@required_permission("expense.view_recurringitem")
def fetch_recurring_items(request):
    """
    AJAX endpoint to fetch recurring item list page rows, paginated and sorted.
    """
    recurring_items = recurring_item_get_data(request)
    current_sort = request.GET.get("sort", "next_due_date")
    return render_paginated_response(
        request=request,
        queryset=recurring_items,
        table_template="expense/partials/recurring_item_fetch.html",
        per_page=10,
        current_sort=current_sort
    )


# ============================================
# RECURRING ITEM WRITE OPERATIONS (CBVs)
# ============================================

class RecurringItemCreateView(RequiredPermissionMixin, CreateView):
    """
    View to create a new recurring item.
    """
    model = RecurringItem
    form_class = RecurringItemForm
    template_name = "expense/recurring_item_form.html"
    success_url = reverse_lazy("expense:recurring_item_list")
    required_permission = "expense.add_recurringitem"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        initial["start_date"] = timezone.localdate()
        initial["next_due_date"] = timezone.localdate()
        initial["active"] = True
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["active_page"] = "recurring"
        context["is_create"] = True
        return context

    def form_valid(self, form):
        form.instance.user = self.request.user
        response = super().form_valid(form)

        RecurringPaymentManager.sync_unpaid_payment(self.object)

        messages.success(self.request, f"Recurring item '{self.object.name}' has been created successfully.")
        return response


class RecurringItemUpdateView(RequiredPermissionMixin, UpdateView):
    """
    View to edit an existing recurring item.
    """
    model = RecurringItem
    form_class = RecurringItemForm
    template_name = "expense/recurring_item_form.html"
    success_url = reverse_lazy("expense:recurring_item_list")
    required_permission = "expense.change_recurringitem"

    def get_queryset(self):
        return RecurringItem.objects.filter(user=self.request.user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["active_page"] = "recurring"
        context["is_create"] = False
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        RecurringPaymentManager.sync_unpaid_payment(self.object)
        messages.success(self.request, f"Recurring item '{self.object.name}' has been updated successfully.")
        return response


class RecurringItemDeleteView(RequiredPermissionMixin, DeleteView):
    """
    View to delete a recurring item (soft delete).
    """
    model = RecurringItem
    template_name = "expense/recurring_item_confirm_delete.html"
    success_url = reverse_lazy("expense:recurring_item_list")
    required_permission = "expense.delete_recurringitem"

    def get_queryset(self):
        return RecurringItem.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["active_page"] = "recurring"
        return context

    def form_valid(self, form):
        success_url = self.get_success_url()
        item_name = self.object.name
        self.object.delete()
        messages.success(self.request, f"Recurring item '{item_name}' has been deleted successfully.")
        return HttpResponseRedirect(success_url)


# ============================================
# RECURRING ITEM DETAIL & CHECKLIST ACTIONS
# ============================================

class RecurringItemDetailView(RequiredPermissionMixin, DetailView):
    """
    View to display detail for a recurring item, showing details and payment checklist.
    """
    model = RecurringItem
    template_name = "expense/recurring_item_detail.html"
    context_object_name = "item"
    required_permission = "expense.view_recurringitem"

    def get_queryset(self):
        return RecurringItem.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["active_page"] = "recurring"

        # Fetch payment history for this recurring item
        payments = self.object.payments.all().order_by("-due_date", "-created_at")
        context["payments"] = payments

        return context


@required_permission("expense.change_recurringpayment")
def toggle_recurring_payment(request, pk):
    """
    Endpoint to toggle payment status of a RecurringPayment.
    """
    payment = get_object_or_404(RecurringPayment, pk=pk, recurring_item__user=request.user)
    if payment.paid:
        RecurringPaymentManager.mark_as_unpaid(payment)
        messages.success(request, f"Payment for {payment.recurring_item.name} ({payment.period_label}) marked as unpaid.")
    else:
        RecurringPaymentManager.mark_as_paid(payment)
        messages.success(request, f"Payment for {payment.recurring_item.name} ({payment.period_label}) marked as paid.")

    # Redirect to referer or detail page
    next_url = request.GET.get("next") or request.POST.get("next")
    if next_url:
        return redirect(next_url)
    return redirect("expense:recurring_item_detail", pk=payment.recurring_item.pk)
