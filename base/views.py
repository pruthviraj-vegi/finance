import logging
from decimal import Decimal
from datetime import timedelta
from django.shortcuts import redirect, render
from django.contrib.auth import logout
from django.contrib import messages
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.utils.http import url_has_allowed_host_and_scheme
from django.db.models import Sum, Q
from django.utils import timezone
from dateutil.relativedelta import relativedelta
import json

from expense.models import Transaction, RecurringPayment, Category
from ledger.models import Transaction as LedgerTransaction, TransactionPayment as LedgerPayment
from .forms import CustomLoginForm

logger = logging.getLogger(__name__)


def home_view(request):
    """Render the main dashboard page."""
    today = timezone.localdate()
    
    # Calculate Income and Expense for the logged-in user
    income_agg = Transaction.objects.filter(user=request.user, type=Transaction.TypeChoices.INCOME).aggregate(total=Sum("amount"))
    expense_agg = Transaction.objects.filter(user=request.user, type=Transaction.TypeChoices.EXPENSE).aggregate(total=Sum("amount"))
    
    total_income = income_agg["total"] or Decimal("0.00")
    total_expense = expense_agg["total"] or Decimal("0.00")
    net_balance = total_income - total_expense
    
    # Calculate pending recurring payments for the logged-in user (only active & not deleted items)
    pending_payments = RecurringPayment.objects.filter(
        recurring_item__user=request.user,
        recurring_item__is_deleted=False,
        recurring_item__active=True,
        paid=False
    ).order_by("due_date")
    pending_count = pending_payments.count()
    pending_amount = pending_payments.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    
    # Calculate trends vs last month
    first_of_this_month = today.replace(day=1)
    first_of_last_month = (first_of_this_month - timedelta(days=1)).replace(day=1)
    end_of_last_month = first_of_this_month - timedelta(days=1)
    
    last_month_income = Transaction.objects.filter(
        user=request.user,
        type=Transaction.TypeChoices.INCOME,
        date__range=(first_of_last_month, end_of_last_month)
    ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    
    last_month_expense = Transaction.objects.filter(
        user=request.user,
        type=Transaction.TypeChoices.EXPENSE,
        date__range=(first_of_last_month, end_of_last_month)
    ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    
    this_month_income = Transaction.objects.filter(
        user=request.user,
        type=Transaction.TypeChoices.INCOME,
        date__range=(first_of_this_month, today)
    ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    
    this_month_expense = Transaction.objects.filter(
        user=request.user,
        type=Transaction.TypeChoices.EXPENSE,
        date__range=(first_of_this_month, today)
    ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    
    if last_month_income > 0:
        income_trend = int(((this_month_income - last_month_income) / last_month_income) * 100)
    else:
        income_trend = 0
        
    if last_month_expense > 0:
        expense_trend = int(((this_month_expense - last_month_expense) / last_month_expense) * 100)
    else:
        expense_trend = 0

    income_trend_is_up = income_trend >= 0
    income_trend_abs = abs(income_trend)
    expense_trend_is_up = expense_trend >= 0
    expense_trend_abs = abs(expense_trend)

    # 12-month data for trend line chart
    months_data = []
    for i in range(11, -1, -1):
        start_of_month = (today - relativedelta(months=i)).replace(day=1)
        if start_of_month.month == 12:
            end_of_month = start_of_month.replace(year=start_of_month.year + 1, month=1) - timedelta(days=1)
        else:
            end_of_month = start_of_month.replace(month=start_of_month.month + 1) - timedelta(days=1)
            
        month_income = Transaction.objects.filter(
            user=request.user,
            type=Transaction.TypeChoices.INCOME,
            date__range=(start_of_month, end_of_month)
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
        
        month_expense = Transaction.objects.filter(
            user=request.user,
            type=Transaction.TypeChoices.EXPENSE,
            date__range=(start_of_month, end_of_month)
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
        
        months_data.append({
            "label": start_of_month.strftime("%b").upper(),
            "income": float(month_income),
            "expense": float(month_expense)
        })

    chart_data = {
        "labels": [m["label"] for m in months_data],
        "income": [m["income"] for m in months_data],
        "expense": [m["expense"] for m in months_data],
    }

    # Calculate category breakdown
    category_breakdown = []
    total_spent_all = Category.objects.filter(user=request.user).annotate(
        total_spent=Sum("transactions__amount", filter=Q(transactions__type=Transaction.TypeChoices.EXPENSE))
    ).aggregate(total=Sum("total_spent"))["total"] or Decimal("0.00")
    
    categories = Category.objects.filter(user=request.user).annotate(
        total_spent=Sum("transactions__amount", filter=Q(transactions__type=Transaction.TypeChoices.EXPENSE))
    ).filter(total_spent__gt=0).order_by("-total_spent")
    
    current_offset = 0.0
    for cat in categories:
        pct = float((cat.total_spent / total_spent_all) * 100) if total_spent_all > 0 else 0.0
        category_breakdown.append({
            "name": cat.name,
            "color": cat.color or "#7C9CFF",
            "amount": float(cat.total_spent),
            "percentage": pct,
            "dash_array": f"{pct:.1f}, 100",
            "dash_offset": f"-{current_offset:.1f}",
        })
        current_offset += pct

    # Loan Portfolio data
    # Owed to you (direction="given", status not settled)
    ledger_lent = LedgerTransaction.objects.filter(user=request.user, direction=LedgerTransaction.DirectionChoices.GIVEN)
    total_lent = ledger_lent.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    repaid_lent = LedgerPayment.objects.filter(transaction__user=request.user, transaction__direction=LedgerTransaction.DirectionChoices.GIVEN).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    owed_to_you = total_lent - repaid_lent
    lent_repaid_pct = int((repaid_lent / total_lent * 100)) if total_lent > 0 else 0
    lent_contracts = ledger_lent.filter(status__in=[LedgerTransaction.StatusChoices.OPEN, LedgerTransaction.StatusChoices.PARTIALLY_SETTLED]).count()

    # You owe (direction="taken", status not settled)
    ledger_borrowed = LedgerTransaction.objects.filter(user=request.user, direction=LedgerTransaction.DirectionChoices.TAKEN)
    total_borrowed = ledger_borrowed.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    repaid_borrowed = LedgerPayment.objects.filter(transaction__user=request.user, transaction__direction=LedgerTransaction.DirectionChoices.TAKEN).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    you_owe = total_borrowed - repaid_borrowed
    borrowed_repaid_pct = int((repaid_borrowed / total_borrowed * 100)) if total_borrowed > 0 else 0
    borrowed_contracts = ledger_borrowed.filter(status__in=[LedgerTransaction.StatusChoices.OPEN, LedgerTransaction.StatusChoices.PARTIALLY_SETTLED]).count()

    # Recent transactions (top 5) for user
    recent_transactions = Transaction.objects.filter(user=request.user).order_by("-date", "-created_at")[:5]
    
    # Upcoming recurring payments (top 5) processed with ring properties
    upcoming_recurring_list = []
    for payment in pending_payments[:5]:
        item = payment.recurring_item
        days_left = (payment.due_date - today).days
        
        if item.type == "emi" and item.total_installments:
            percent = (item.installments_paid or 0) / item.total_installments * 100
        else:
            percent = max(0, min(100, (30 - days_left) / 30 * 100)) if days_left >= 0 else 100

        # Circumference of r=20 is 125.66. We match dashboard_compact.html using 125.6
        dash_offset = 125.6 * (1 - (percent / 100))

        icon = "event_repeat"
        if item.type == "emi":
            icon = "account_balance"
        elif item.type == "subscription":
            icon = "cloud"
        elif item.type == "renewal":
            icon = "shield"

        if days_left == 0:
            due_text = "Due today"
        elif days_left == 1:
            due_text = "Due tomorrow"
        elif days_left < 0:
            due_text = f"Overdue by {abs(days_left)} day{'s' if abs(days_left) > 1 else ''}"
        else:
            due_text = f"Due in {days_left} day{'s' if days_left > 1 else ''}"

        upcoming_recurring_list.append({
            "id": payment.pk,
            "name": item.name,
            "amount": payment.amount,
            "type_display": item.get_type_display(),
            "due_text": due_text,
            "percent": int(percent),
            "dash_offset": f"{dash_offset:.1f}",
            "icon": icon,
        })

    context = {
        "active_page": "dashboard",
        "total_income": total_income,
        "total_expense": total_expense,
        "net_balance": net_balance,
        "pending_count": pending_count,
        "pending_amount": pending_amount,
        
        "income_trend_is_up": income_trend_is_up,
        "income_trend_abs": income_trend_abs,
        "expense_trend_is_up": expense_trend_is_up,
        "expense_trend_abs": expense_trend_abs,
        
        "category_breakdown": category_breakdown,
        "chart_data_json": json.dumps(chart_data),
        
        "owed_to_you": owed_to_you,
        "lent_repaid_pct": lent_repaid_pct,
        "lent_contracts": lent_contracts,
        
        "you_owe": you_owe,
        "borrowed_repaid_pct": borrowed_repaid_pct,
        "borrowed_contracts": borrowed_contracts,
        
        "recent_transactions": recent_transactions,
        "upcoming_recurring": upcoming_recurring_list,
    }
    return render(request, "base/home.html", context)


class CustomLoginView(LoginView):
    """Handle user login with remember-me and safe redirect support."""

    form_class = CustomLoginForm
    template_name = "base/login.html"
    redirect_authenticated_user = True

    def get_success_url(self):
        """
        Redirect to the exact page after login.
        Priority:
        1. 'next' parameter from POST request (form submission)
        2. 'next' URL parameter from GET request
        3. 'next' stored in session (by middleware)
        4. Default to home page
        """
        redirect_url = self.request.POST.get("next") or self.request.GET.get("next")

        # If not in GET/POST, check session (stored by middleware)
        if not redirect_url:
            redirect_url = self.request.session.get("next")
            # Clean up session after retrieving
            if redirect_url:
                del self.request.session["next"]

        # Validate the redirect URL for security
        if redirect_url:
            # Check if URL is safe (same host, allowed scheme)
            if url_has_allowed_host_and_scheme(redirect_url, allowed_hosts=None):
                return redirect_url

        # Default to home page
        return reverse_lazy("base:home")

    def form_valid(self, form):
        remember = form.cleaned_data.get("remember")
        if not remember:
            # Set session to expire when browser closes
            self.request.session.set_expiry(0)

        # Call parent form_valid to handle login
        response = super().form_valid(form)

        # Add success message
        messages.success(self.request, f"Welcome back, {self.request.user.full_name}!")

        return response

    def form_invalid(self, form):
        # Add error message for invalid login
        messages.error(
            self.request, "Invalid phone number or password. Please try again."
        )

        return super().form_invalid(form)


def logout_view(request):
    """Logout and redirect to login page."""
    logout(request)
    messages.success(request, "You have been signed out successfully.")
    return redirect("base:login")
