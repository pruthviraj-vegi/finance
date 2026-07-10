from django.contrib import admin
from .models import Category, RecurringItem, RecurringPayment
from .models import Transaction as ExpenseTransaction


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "color", "is_deleted", "created_at")
    list_filter = ("is_deleted", "user")
    search_fields = ("name", "user__first_name", "user__phone_number")


@admin.register(ExpenseTransaction)
class ExpenseTransactionAdmin(admin.ModelAdmin):
    list_display = ("user", "type", "amount", "category", "date", "is_deleted")
    list_filter = ("type", "is_deleted", "user")
    search_fields = ("note", "category__name", "user__first_name", "user__phone_number")
    date_hierarchy = "date"


@admin.register(RecurringItem)
class RecurringItemAdmin(admin.ModelAdmin):
    list_display = ("name", "type", "user", "amount", "frequency", "next_due_date", "active", "is_deleted")
    list_filter = ("type", "frequency", "active", "is_deleted", "user")
    search_fields = ("name", "user__first_name", "user__phone_number")


@admin.register(RecurringPayment)
class RecurringPaymentAdmin(admin.ModelAdmin):
    list_display = ("recurring_item", "period_label", "due_date", "amount", "paid", "is_deleted")
    list_filter = ("paid", "is_deleted")
    search_fields = ("recurring_item__name", "period_label")
