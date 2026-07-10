from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    list_display = ("phone_number", "first_name", "last_name", "email", "is_staff", "is_active", "is_deleted")
    list_filter = ("is_staff", "is_active", "is_deleted", "groups")
    search_fields = ("phone_number", "first_name", "last_name", "email")
    ordering = ("first_name", "last_name")
    readonly_fields = ("last_login",)

    fieldsets = (
        (None, {"fields": ("phone_number", "password")}),
        ("Personal Info", {"fields": ("first_name", "last_name", "email", "address")}),
        ("Permissions", {"fields": ("is_staff", "is_active", "is_superuser", "groups", "user_permissions")}),
        ("Soft Delete", {"fields": ("is_deleted", "deleted_at")}),
        ("Important Dates", {"fields": ("last_login",)}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("phone_number", "first_name", "last_name", "password1", "password2", "is_staff", "is_active"),
        }),
    )
