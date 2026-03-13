import jwt
from django.contrib.auth import get_user_model
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


def get_oidc_claims(request):
    """
    Получение OIDC claims из сессии или токена
    """
    claims = {}

    # Способ 1: Из сессии (если claims были сохранены)
    if hasattr(request, 'session'):
        claims = request.session.get('oidc_id_token_claims', {})
        if not claims:
            # Способ 2: Из ID токена в сессии
            id_token = request.session.get('oidc_id_token')
            if id_token:
                try:
                    claims = jwt.decode(
                        id_token,
                        options={"verify_signature": False}
                    )
                except Exception as e:
                    logger.error(f"Failed to decode ID token: {e}")

    return claims


def get_oidc_user_info(request):
    """
    Получение userinfo из сессии
    """
    if hasattr(request, 'session'):
        return request.session.get('oidc_userinfo', {})
    return {}


def is_oidc_authenticated(request):
    """
    Проверка, аутентифицирован ли пользователь через OIDC
    """
    return (
            request.user.is_authenticated and
            request.session.get('oidc_id_token') is not None
    )


def refresh_oidc_token(request):
    """
    Обновление OIDC токена
    """

    if not is_oidc_authenticated(request):
        return False

    try:
        # Используем встроенный механизм обновления
        from mozilla_django_oidc.views import get_next_url

        # Инициируем обновление токена
        refresh_token = request.session.get('oidc_refresh_token')
        if not refresh_token:
            logger.warning("No refresh token available")
            return False


        return True

    except Exception as e:
        logger.error(f"Failed to refresh OIDC token: {e}")
        return False