from django.urls import path
from . import views

app_name = "ledger"

urlpatterns = [
    # Contacts
    path("", views.contact_home, name="contact_list"),
    path("fetch/", views.fetch_contacts, name="contact_fetch"),
    path("create/", views.ContactCreateView.as_view(), name="contact_create"),
    path("<int:pk>/", views.ContactDetailView.as_view(), name="contact_detail"),
    path("<int:pk>/update/", views.ContactUpdateView.as_view(), name="contact_update"),
    path("<int:pk>/delete/", views.ContactDeleteView.as_view(), name="contact_delete"),

    # Transactions
    path("transactions/", views.transaction_home, name="transaction_list"),
    path("transactions/fetch/", views.fetch_transactions, name="transaction_fetch"),
    path("transactions/create/", views.TransactionCreateView.as_view(), name="transaction_create"),
    path("transactions/<int:pk>/update/", views.TransactionUpdateView.as_view(), name="transaction_update"),
    path("transactions/<int:pk>/delete/", views.TransactionDeleteView.as_view(), name="transaction_delete"),

    # Payments / Repayments
    path("payments/create/", views.TransactionPaymentCreateView.as_view(), name="payment_create"),
    path("payments/<int:pk>/update/", views.TransactionPaymentUpdateView.as_view(), name="payment_update"),
    path("payments/<int:pk>/delete/", views.TransactionPaymentDeleteView.as_view(), name="payment_delete"),
]
