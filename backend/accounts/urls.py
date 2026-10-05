from django.urls import path
from .views import AreaView, CsrfView, LoginView, LogoutView, MeView

urlpatterns = [
    path("auth/csrf/", CsrfView.as_view()),
    path("auth/login/", LoginView.as_view()),
    path("auth/me/", MeView.as_view()),
    path("auth/logout/", LogoutView.as_view()),
    path("staff/access/", AreaView.as_view(required_permission="accounts.access_staff")),
    path("kitchen/access/", AreaView.as_view(required_permission="accounts.access_kitchen")),
    path("bar/access/", AreaView.as_view(required_permission="accounts.access_bar")),
]
