from django.urls import path
from .views import DashboardView, McpDashboardView, McpSalesSummaryView

urlpatterns = [
    path("dashboard/summary/", DashboardView.as_view()),
    path("mcp/dashboard/", McpDashboardView.as_view()),
    path("mcp/sales/summary/", McpSalesSummaryView.as_view()),
]
