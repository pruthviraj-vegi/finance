from django.urls import path
from expense import views

app_name = "expense"

urlpatterns = [
    # Category URLS
    path("categories/", views.category_home, name="category_list"),
    path("categories/fetch/", views.fetch_categories, name="fetch_categories"),
    path(
        "categories/create/", views.CategoryCreateView.as_view(), name="category_create"
    ),
    path(
        "categories/<int:pk>/update/",
        views.CategoryUpdateView.as_view(),
        name="category_update",
    ),
    path(
        "categories/<int:pk>/delete/",
        views.CategoryDeleteView.as_view(),
        name="category_delete",
    ),
    # Transaction URLS
    path("transactions/", views.transaction_home, name="transaction_list"),
    path("transactions/fetch/", views.fetch_transactions, name="fetch_transactions"),
    path(
        "transactions/create/",
        views.TransactionCreateView.as_view(),
        name="transaction_create",
    ),
    path(
        "transactions/<int:pk>/update/",
        views.TransactionUpdateView.as_view(),
        name="transaction_update",
    ),
    path(
        "transactions/<int:pk>/delete/",
        views.TransactionDeleteView.as_view(),
        name="transaction_delete",
    ),
    # Recurring Item URLS
    path("recurring/dashboard/", views.recurring_dashboard, name="recurring_dashboard"),
    path("recurring/", views.recurring_item_home, name="recurring_item_list"),
    path("recurring/fetch/", views.fetch_recurring_items, name="fetch_recurring_items"),
    path(
        "recurring/create/",
        views.RecurringItemCreateView.as_view(),
        name="recurring_item_create",
    ),
    path(
        "recurring/<int:pk>/update/",
        views.RecurringItemUpdateView.as_view(),
        name="recurring_item_update",
    ),
    path(
        "recurring/<int:pk>/delete/",
        views.RecurringItemDeleteView.as_view(),
        name="recurring_item_delete",
    ),
    path(
        "recurring/<int:pk>/",
        views.RecurringItemDetailView.as_view(),
        name="recurring_item_detail",
    ),
    # Recurring Payment Checklist URL
    path(
        "recurring/payment/<int:pk>/toggle/",
        views.toggle_recurring_payment,
        name="toggle_recurring_payment",
    ),
]
