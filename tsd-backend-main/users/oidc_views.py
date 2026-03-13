"""
OIDC аутентификация через SLB ADFS.

Флоу:
  1. GET /auth/login      → редирект на ADFS (browser redirect)
  2. GET /auth/callback   → обмен code на token, создание сессии, редирект на /
  3. GET /auth/me         → проверка сессии, возврат данных пользователя
  4. GET /auth/logout     → очистка сессии

Сессии хранятся в таблице tsdb_sessions в БД через Django session framework.
"""
import secrets
import logging
from urllib.parse import urlencode

import requests
import jwt
from django.conf import settings
from django.http import HttpResponseRedirect, JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
#  Session store через Django session framework → таблица tsdb_sessions в БД
# --------------------------------------------------------------------------- #
SESSION_TIMEOUT = 43200  # 12 часов в секундах
SESSION_COOKIE_NAME = "session_token"


def _create_session(user_data: dict) -> str:
    """
    Создаёт сессию в БД (tsdb_sessions) и возвращает session_key.
    Используется и OIDC callback, и LDAP login.
    """
    from tsdp_backend.session_backend import SessionStore
    store = SessionStore()
    store["authenticated"] = True
    store["user"] = user_data
    store.set_expiry(SESSION_TIMEOUT)
    store.create()
    logger.info(f"Session created in DB for alias='{user_data.get('alias')}', key={store.session_key[:8]}...")
    return store.session_key


def _get_session(request) -> dict | None:
    """
    Читает сессию из БД по session_token cookie.
    Возвращает данные сессии или None если сессия не найдена / истекла.
    """
    from tsdp_backend.session_backend import SessionStore
    token = request.COOKIES.get(SESSION_COOKIE_NAME)
    if not token:
        return None
    from tsdp_backend.session_backend import SessionStore
    store = SessionStore(session_key=token)
    # exists() проверяет наличие в БД и что не истекла
    if not store.exists(token):
        return None
    try:
        authenticated = store.get("authenticated")
        user = store.get("user")
    except Exception:
        return None
    if not authenticated or not user:
        return None
    return {"authenticated": authenticated, "user": user}


def _extract_user_info(tokens: dict) -> dict:
    """
    Извлекает данные пользователя из токенов ADFS.

    ADFS кладёт claims либо в id_token, либо в access_token.
    Пробуем оба, мёржим, достаём alias из unique_name / upn / email.
    """
    claims = {}

    for key in ("id_token", "access_token"):
        token = tokens.get(key)
        if not token:
            continue
        try:
            decoded = jwt.decode(token, options={"verify_signature": False})
            logger.info(f"{key} claims keys: {list(decoded.keys())}")
            claims.update(decoded)
        except Exception as e:
            logger.warning(f"Cannot decode {key}: {e}")

    # Достаём alias по приоритету: unique_name → upn → email
    alias = ""
    unique_name = claims.get("unique_name", "")
    upn = claims.get("upn", "")
    email = claims.get("email", "")

    if unique_name:
        raw = unique_name.split("\\")[-1] if "\\" in unique_name else unique_name
        alias = raw[:2].upper() + raw[2:].lower() if len(raw) >= 2 else raw.upper()
    elif upn and "@" in upn:
        raw = upn.split("@")[0]
        alias = raw[:2].upper() + raw[2:].lower() if len(raw) >= 2 else raw.upper()
    elif email and "@" in email:
        raw = email.split("@")[0]
        alias = raw[:2].upper() + raw[2:].lower() if len(raw) >= 2 else raw.upper()

    logger.info(f"Extracted alias='{alias}', email='{email}', upn='{upn}', unique_name='{unique_name}'")

    return {
        "alias": alias,
        "email": email,
        "upn": upn,
        "unique_name": unique_name,
        "sub": claims.get("sub", ""),
        "given_name": claims.get("given_name", claims.get("first_name", "")),
        "family_name": claims.get("family_name", claims.get("last_name", "")),
        "raw_claims": claims,
    }


# --------------------------------------------------------------------------- #
#  Views
# --------------------------------------------------------------------------- #

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status as drf_status


class OIDCAuthenticateAPIView(APIView):
    """
    GET /api/portal/oidc/authenticate/
    Возвращает JSON { auth_url: "..." } — фронт делает window.location.href = auth_url.
    Используется если фронт сначала делает fetch, а потом редиректит.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        state = secrets.token_urlsafe(16)
        request.session["oidc_state"] = state

        params = {
            "client_id": settings.OIDC_RP_CLIENT_ID,
            "response_type": "code",
            "scope": settings.OIDC_RP_SCOPES,
            "redirect_uri": settings.OIDC_REDIRECT_URI,
            "state": state,
        }
        auth_url = f"{settings.OIDC_OP_AUTHORIZATION_ENDPOINT}?{urlencode(params)}"
        logger.info(f"OIDC authenticate: returning auth_url to frontend")
        return Response({"auth_url": auth_url}, status=drf_status.HTTP_200_OK)


class LoginView(View):
    """
    GET /auth/login
    Делает 302 редирект прямо на ADFS — фронт просто делает window.location.href = '/auth/login'
    """

    def get(self, request):
        state = secrets.token_urlsafe(16)
        # Сохраняем state в Django-сессии для валидации при callback
        request.session["oidc_state"] = state

        params = {
            "client_id": settings.OIDC_RP_CLIENT_ID,
            "response_type": "code",
            "scope": settings.OIDC_RP_SCOPES,
            "redirect_uri": settings.OIDC_REDIRECT_URI,
            "state": state,
        }
        auth_url = f"{settings.OIDC_OP_AUTHORIZATION_ENDPOINT}?{urlencode(params)}"
        logger.info(f"Redirecting to ADFS: {auth_url}")
        return HttpResponseRedirect(auth_url)


@method_decorator(csrf_exempt, name="dispatch")
class CallbackView(View):
    """
    GET /auth/callback
    ADFS присылает code в query params. Обмениваем на token, создаём сессию.
    """

    def get(self, request):
        error = request.GET.get("error")
        if error:
            desc = request.GET.get("error_description", "")
            logger.error(f"ADFS error: {error} — {desc}")
            return JsonResponse({"error": error, "description": desc}, status=400)

        code = request.GET.get("code")
        state = request.GET.get("state")

        if not code:
            logger.error("Missing authorization code")
            return JsonResponse({"error": "missing_code"}, status=400)

        # Валидация state (защита CSRF)
        # В dev можно отключить — просто логируем несовпадение
        session_state = request.session.get("oidc_state")
        if session_state and state != session_state:
            logger.warning(f"State mismatch: expected={session_state}, got={state}")
            # В prod раскомментировать:
            # return JsonResponse({"error": "invalid_state"}, status=400)

        # Обмен code на токены
        token_data = {
            "grant_type": "authorization_code",
            "client_id": settings.OIDC_RP_CLIENT_ID,
            "client_secret": settings.OIDC_RP_CLIENT_SECRET,
            "code": code,
            "redirect_uri": settings.OIDC_REDIRECT_URI,
        }
        logger.debug(f"Exchanging code for token at {settings.OIDC_OP_TOKEN_ENDPOINT}")

        try:
            resp = requests.post(
                settings.OIDC_OP_TOKEN_ENDPOINT,
                data=token_data,
                headers={"Accept": "application/json"},
                timeout=30,
                verify=False,  # ADFS может использовать внутренний сертификат
            )
            logger.info(f"Token endpoint response: {resp.status_code}")
            if resp.status_code != 200:
                logger.error(f"Token exchange failed: {resp.text[:500]}")
                return JsonResponse({"error": "token_exchange_failed", "detail": resp.text[:200]}, status=400)
            tokens = resp.json()
        except requests.RequestException as e:
            logger.error(f"Request to token endpoint failed: {e}")
            return JsonResponse({"error": "token_request_failed", "detail": str(e)}, status=500)

        # Извлекаем данные пользователя из токенов
        try:
            user_info = _extract_user_info(tokens)
        except Exception as e:
            logger.error(f"Failed to extract user info: {e}", exc_info=True)
            return JsonResponse({"error": "user_info_extraction_failed", "detail": str(e)}, status=400)

        if not user_info.get("alias"):
            logger.error(f"Could not determine alias from claims: {list(user_info.get('raw_claims', {}).keys())}")
            return JsonResponse({
                "error": "no_alias",
                "claims_keys": list(user_info.get("raw_claims", {}).keys()),
            }, status=400)

        # Ищем пользователя в БД по alias (iexact — регистронезависимо)
        from .models import Users
        try:
            db_user = Users.objects.get(alias__iexact=user_info["alias"], is_active=True)
        except Users.DoesNotExist:
            logger.error(f"User with alias='{user_info['alias']}' not found in DB")
            return JsonResponse({
                "error": "user_not_found",
                "tried_alias": user_info["alias"],
                "hint": "User must be pre-created by admin",
            }, status=401)
        except Users.MultipleObjectsReturned:
            logger.warning(f"Multiple users with alias='{user_info['alias']}', taking first")
            db_user = Users.objects.filter(alias__iexact=user_info["alias"], is_active=True).first()

        # Создаём сессию
        session_payload = {
            "alias": db_user.alias,
            "email": db_user.email,
            "first_name": db_user.first_name,
            "second_name": db_user.second_name,
            "job_title": db_user.job_title,
            "is_manager": db_user.is_manager,
            "id": db_user.id,
        }
        session_token = _create_session(session_payload)

        frontend_url = getattr(settings, 'FRONTEND_URL', '')
        redirect_target = f"{frontend_url}/login?oidc=1"
        logger.info(f"User '{db_user.alias}' authenticated successfully, redirecting to {redirect_target}")
        response = HttpResponseRedirect(redirect_target)
        response.set_cookie(
            key=SESSION_COOKIE_NAME,
            value=session_token,
            httponly=True,
            secure=True,
            samesite=getattr(settings, 'COOKIE_SAMESITE', 'Lax'),
            max_age=SESSION_TIMEOUT,
        )
        return response


class MeView(View):
    """
    GET /api/portal/auth/me/
    Проверяет session_token cookie. Возвращает данные пользователя или 401.
    """

    def get(self, request):
        session = _get_session(request)
        if not session:
            return JsonResponse({"authenticated": False}, status=401)

        return JsonResponse({
            "authenticated": True,
            "user": session["user"],
        })


@method_decorator(csrf_exempt, name="dispatch")
class LogoutView(View):
    """
    GET /auth/logout
    Удаляет сессию и cookie, редиректит на /login (или /auth/login для нового входа).
    """

    def get(self, request):
        token = request.COOKIES.get(SESSION_COOKIE_NAME)
        if token:
            from tsdp_backend.session_backend import SessionStore
            SessionStore(session_key=token).delete()
            logger.info(f"Session {token[:8]}... deleted from DB")

        # Очищаем также стандартную Django-сессию (хранит oidc_state)
        request.session.flush()

        response = HttpResponseRedirect("/login")
        response.delete_cookie(SESSION_COOKIE_NAME)
        return response
