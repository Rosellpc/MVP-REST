from django.urls import path
from .views import DashboardView

urlpatterns = [path("dashboard/summary/", DashboardView.as_view())]
