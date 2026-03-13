from django.urls import path
from rest_framework_simplejwt.views import TokenVerifyView
from .views import (
    UsersListCreateView,
    UsersRetrieveView,
    UsersUpdateView,
    UsersDestroyView,
    TeamsListCreateView,
    TeamsRetrieveUpdateDestroyView,
    DesksListCreateView,
    DesksRetrieveUpdateDestroyView,
    LoginView,
    LDAPLoginView,
    RefreshTokenView,
    LogoutView,
    OIDCConfigDiagnosticView,
    SyncEmployeeDataView,
)
from .oidc_views import MeView, OIDCAuthenticateAPIView
from django.views.generic import TemplateView

urlpatterns = [
    # JWT manual login (username/password)
    path('auth/login/', LoginView.as_view(), name='login'),
    # LDAP / Active Directory login
    path('auth/ldap/', LDAPLoginView.as_view(), name='ldap_login'),
    path('auth/refresh/', RefreshTokenView.as_view(), name='token_refresh'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('auth/verify/', TokenVerifyView.as_view(), name='token_verify'),
    # Session check (uses session_token cookie set by OIDC callback)
    path('auth/me/', MeView.as_view(), name='auth_me'),
    # OIDC: frontend fetches this → gets {auth_url} → does window.location.href = auth_url
    path('oidc/authenticate/', OIDCAuthenticateAPIView.as_view(), name='oidc_authenticate'),

    path('users/', UsersListCreateView.as_view(), name='users-list-create'),
    path('users/<int:pk>/', UsersRetrieveView.as_view(), name='users-detail'),
    path('users/<int:pk>/', UsersUpdateView.as_view(), name='users-update'),
    path('users/<int:pk>/', UsersDestroyView.as_view(), name='users-delete'),

    path('sync-employees/', SyncEmployeeDataView.as_view(), name='sync-employees-get'),

    path('teams/', TeamsListCreateView.as_view(), name='teams-list-create'),
    path('teams/<int:pk>/', TeamsRetrieveUpdateDestroyView.as_view(), name='teams-create-update-destroy'),

    path('desks/', DesksListCreateView.as_view(), name='desks-list-create'),
    path('desks/<int:pk>/', DesksRetrieveUpdateDestroyView.as_view(), name='desks-create-update-destroy'),

    path('oidc/diagnostic/', OIDCConfigDiagnosticView.as_view(), name='oidc_diagnostic'),

    path('', TemplateView.as_view(template_name='home.html'), name='home'),
    path('login-success/', TemplateView.as_view(template_name='login_success.html'), name='login_success'),
    path('login-error/', TemplateView.as_view(template_name='login_error.html'), name='login_error'),
]
from django.conf import settings
from django.conf.urls.static import static

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)