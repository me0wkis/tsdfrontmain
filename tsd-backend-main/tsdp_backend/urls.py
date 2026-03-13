from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

from users.oidc_views import LoginView as OIDCLoginView, CallbackView as OIDCCallbackView, LogoutView as OIDCLogoutView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    path('api/portal/', include('users.urls')),
    path('api/portal/', include('shifts.urls')),

    # OIDC flow (browser-level, не API)
    # Фронт: window.location.href = '/auth/login'
    path('auth/login', OIDCLoginView.as_view(), name='oidc_login'),
    path('auth/login/', OIDCLoginView.as_view(), name='oidc_login_slash'),
    # ADFS callback (зарегистрирован в ADFS как /auth/callback)
    path('auth/callback', OIDCCallbackView.as_view(), name='oidc_callback'),
    path('auth/callback/', OIDCCallbackView.as_view(), name='oidc_callback_slash'),
    # Logout
    path('auth/logout', OIDCLogoutView.as_view(), name='oidc_logout'),
    path('auth/logout/', OIDCLogoutView.as_view(), name='oidc_logout_slash'),
]
