from django.urls import path
from .views import StaffOrderList, ReleaseOrderView, TicketList, TicketDetail, TicketAction, ApproveCancellationView, CancellationNotices

urlpatterns = [
    path("staff/orders/<int:pk>/cancel/", ApproveCancellationView.as_view()),
    path("production/cancellation-notices/", CancellationNotices.as_view()),
    path("production/tickets/<int:pk>/finalize/", TicketAction.as_view(target_status="FINALIZED")),
    path("staff/orders/", StaffOrderList.as_view()),
    path("staff/orders/<int:pk>/release/", ReleaseOrderView.as_view()),
    path("production/tickets/", TicketList.as_view()),
    path("production/tickets/<int:pk>/", TicketDetail.as_view()),
    path("production/tickets/<int:pk>/start/", TicketAction.as_view(target_status="IN_PROGRESS")),
    path("production/tickets/<int:pk>/complete/", TicketAction.as_view(target_status="READY")),
    path("production/tickets/<int:pk>/cancel/", TicketAction.as_view(target_status="CANCELLED")),
]
