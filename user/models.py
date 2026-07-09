"""Models for the user app."""

from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils.translation import gettext_lazy as _

from base.manager import SoftDeleteModel
from base.utility import StringProcessor

from .managers import CustomUserManager

User = settings.AUTH_USER_MODEL


class CustomUser(AbstractBaseUser, PermissionsMixin, SoftDeleteModel):
    """Custom User model for the application."""

    first_name = models.CharField(max_length=255, null=True, blank=True)
    last_name = models.CharField(max_length=255, null=True, blank=True)

    email = models.EmailField(
        max_length=255,
        unique=True,
        null=True,
        blank=True,
        verbose_name=_("Email Address (Optional)"),
        help_text=_("Optional email address. Leave blank if not needed."),
    )
    phone_number = models.CharField(
        max_length=15, unique=True, verbose_name=_("Phone Number")
    )
    address = models.TextField(max_length=255, null=True, blank=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    # --- ADDED TO FIX MIGRATION ERROR ---
    # These fields are required to avoid clashes with the default User model's
    # reverse accessors when you have a custom user model.
    groups = models.ManyToManyField(
        "auth.Group",
        verbose_name=_("groups"),
        blank=True,
        help_text=_(
            "The groups this user belongs to. A user will get all permissions "
            "granted to each of their groups."
        ),
        related_name="customuser_set",  # Unique related_name
        related_query_name="user",
    )
    user_permissions = models.ManyToManyField(
        "auth.Permission",
        verbose_name=_("user permissions"),
        blank=True,
        help_text=_("Specific permissions for this user."),
        related_name="customuser_permissions_set",  # Unique related_name
        related_query_name="user",
    )

    USERNAME_FIELD = "phone_number"
    REQUIRED_FIELDS = ["first_name"]
    objects = CustomUserManager()

    def save(self, *args, **kwargs):

        self.first_name = StringProcessor(self.first_name).toTitle()
        self.last_name = StringProcessor(self.last_name).toTitle()
        self.email = StringProcessor(self.email).toLowercase()
        self.address = StringProcessor(self.address).toTitle()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.phone_number})"

    @property
    def username(self):
        """Return the username of the user (first name)."""
        return self.first_name

    @property
    def full_name(self):
        """Return the full name of the user."""
        return str(self.first_name) + " " + str(self.last_name)

    class Meta:
        """Meta class for CustomUser."""

        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ["first_name", "last_name"]
        permissions = [("view_dashboard", "Can view user dashboard")]
