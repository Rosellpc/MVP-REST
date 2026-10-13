from django.urls import path
from .views import PreparePaymentView, PaymentDetailView, PaymentConfigView, ChargeView, ReconcileView, WebhookView, PaymentQuoteView, AbandonPaymentView

urlpatterns = [
    path("payments/config/", PaymentConfigView.as_view()),
    path("payments/preview/", PaymentQuoteView.as_view()),
    path("payments/culqi/webhook/", WebhookView.as_view()),
    path("payments/<uuid:public_code>/charge/", ChargeView.as_view()),
    path("payments/<uuid:public_code>/reconcile/", ReconcileView.as_view()),
    path("payments/<uuid:public_code>/abandon/", AbandonPaymentView.as_view()),
    path("payments/prepare/", PreparePaymentView.as_view()),
    path("payments/<uuid:public_code>/", PaymentDetailView.as_view()),
]
