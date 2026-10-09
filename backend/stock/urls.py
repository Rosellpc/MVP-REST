from django.urls import path
from .views import DashboardView, ActionView, HistoryView, ShiftsView, ShiftDetailView

urlpatterns = [
    path("stock/", DashboardView.as_view()),
    path("stock/open/", ActionView.as_view(action="open")),
    path("stock/movements/", ActionView.as_view(action="movement")),
    path("stock/close/", ActionView.as_view(action="close")),
    path("stock/history/", HistoryView.as_view()),
    path("stock/shifts/", ShiftsView.as_view()),
    path("stock/shifts/<int:pk>/", ShiftDetailView.as_view()),
]
