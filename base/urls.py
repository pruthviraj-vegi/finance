from django.urls import path
from . import views

app_name = "base"

urlpatterns = [
    path("", views.home_view, name="home"),
    path("login/", views.CustomLoginView.as_view(), name="login"),
    path("logout/", views.logout_view, name="logout"),
]

