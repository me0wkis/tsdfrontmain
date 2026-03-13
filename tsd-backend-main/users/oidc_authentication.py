"""
DRF authentication backend для OIDC/LDAP-сессий.

Проверяет session_token cookie против in-memory хранилища _sessions
(тот же механизм, что используют OIDC callback и LDAP login).
Это позволяет всем DRF-вьюхам с IsAuthenticated работать
с нашей сессионной авторизацией без JWT.
"""
import logging
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

logger = logging.getLogger(__name__)


class OIDCSessionAuthentication(BaseAuthentication):
    """
    Аутентификация через session_token cookie (in-memory store).
    Работает для сессий созданных как через OIDC callback, так и через LDAP login.
    """

    def authenticate(self, request):
        # Импорт внутри метода во избежание circular import при старте Django
        from .oidc_views import _get_session

        session = _get_session(request)
        if not session or not session.get("authenticated"):
            return None

        user_data = session.get("user", {})
        user_id = user_data.get("id")
        if not user_id:
            return None

        from .models import Users
        try:
            user = Users.objects.get(pk=user_id)
        except Users.DoesNotExist:
            logger.warning(f"OIDCSessionAuthentication: user id={user_id} not found in DB")
            raise AuthenticationFailed("User not found")

        return (user, None)  # (user, auth_token)

    def authenticate_header(self, request):
        return "Session"
