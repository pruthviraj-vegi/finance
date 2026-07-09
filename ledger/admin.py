from django.contrib import admin
from .models import Contact, Transaction, TransactionPayment


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ("name", "phone_number", "user", "is_deleted", "created_at")
    list_filter = ("is_deleted", "user")
    search_fields = ("name", "phone_number", "notes", "user__first_name", "user__phone_number")


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("contact", "direction", "amount", "date", "status", "user", "is_deleted")
    list_filter = ("direction", "status", "is_deleted", "user")
    search_fields = ("reason", "contact__name", "user__first_name", "user__phone_number")


@admin.register(TransactionPayment)
class TransactionPaymentAdmin(admin.ModelAdmin):
    list_display = ("transaction", "amount", "date", "is_deleted")
    list_filter = ("is_deleted",)
    search_fields = ("note", "transaction__contact__name")
