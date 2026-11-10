"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from .health import health
from accounts.mcp_auth import StaffOAuthLoginView, oauth_connected, oauth_metadata

urlpatterns = [
    path('.well-known/oauth-authorization-server', oauth_metadata),
    path('oauth/login/', StaffOAuthLoginView.as_view(), name='mcp-oauth-login'),
    path('oauth/connected/', oauth_connected, name='mcp-oauth-connected'),
    path('o/', include('oauth2_provider.urls', namespace='oauth2_provider')),
    path('api/health/', health),
    path('api/v1/', include('payments.urls')),
    path('api/v1/', include('analytics.urls')),
    path('api/v1/', include('stock.urls')),
    path('api/v1/', include('costing.urls')),
    path('api/v1/', include('production.urls')),
    path('api/v1/', include('accounts.urls')),
    path('admin/', admin.site.urls),
    path('api/v1/', include('catalog.urls')),
    path('api/v1/', include('orders.urls')),
]
