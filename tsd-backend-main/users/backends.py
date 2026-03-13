from django.contrib.auth.backends import BaseBackend
from rest_framework_simplejwt.authentication import JWTAuthentication
from mozilla_django_oidc.auth import OIDCAuthenticationBackend
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
import logging

from .models import Users

logger = logging.getLogger(__name__)
User = get_user_model()


class OIDCAuthenticationBackend(OIDCAuthenticationBackend):
    """Кастомный бэкенд для SLB ADFS с обработкой unique_name"""

    def filter_users_by_claims(self, claims):
        """
        Фильтрация пользователей по claims из ADFS.
        Берём email из claims и отбрасываем часть после @,
        получаем alias напрямую без преобразований регистра.
        """
        # Приоритет: email → upn → unique_name
        email = claims.get('email', '')
        upn = claims.get('upn', '')
        unique_name = claims.get('unique_name', '')

        # Выбираем источник для alias
        if email and '@' in email:
            raw_alias = email.split('@')[0]
            source = f"email={email}"
        elif upn and '@' in upn:
            raw_alias = upn.split('@')[0]
            source = f"upn={upn}"
        elif unique_name:
            raw_alias = unique_name.split('\\')[-1] if '\\' in unique_name else unique_name
            if '@' in raw_alias:
                raw_alias = raw_alias.split('@')[0]
            source = f"unique_name={unique_name}"
        else:
            logger.warning(f"No email, upn or unique_name in claims. Available keys: {list(claims.keys())}")
            return self.UserModel.objects.none()

        logger.info(f"Looking up user by alias='{raw_alias}' (from {source})")

        # Ищем пользователя по alias без учёта регистра
        users = self.UserModel.objects.filter(alias__iexact=raw_alias)
        if not users.exists():
            all_aliases = list(self.UserModel.objects.values_list('alias', flat=True))
            logger.warning(f"User with alias='{raw_alias}' not found. Aliases in DB: {all_aliases}")
        return users

    def create_user(self, claims):
        """
        Создание нового пользователя НЕ поддерживается.
        Пользователи должны быть предварительно добавлены в БД администратором.
        Вход разрешён только существующим пользователям.
        """
        unique_name = claims.get('unique_name', '') or claims.get('upn', '') or claims.get('email', '')
        raw_alias = unique_name.split('\\')[-1] if '\\' in unique_name else unique_name
        if '@' in raw_alias:
            raw_alias = raw_alias.split('@')[0]
        alias = raw_alias[:2].upper() + raw_alias[2:].lower() if len(raw_alias) >= 2 else raw_alias.upper()

        logger.error(
            f"OIDC login failed: user '{alias}' authenticated via ADFS but not found in the database. "
            f"An administrator must add this user first."
        )
        return None
        return user

    def update_user(self, user, claims):
        """
        Обновление пользователя из ADFS claims
        """
        # Обновляем email если изменился
        email = claims.get('email')
        if email and user.email != email:
            user.email = email
        
        # Обновляем имя/фамилию
        given_name = claims.get('given_name', '')
        family_name = claims.get('family_name', '')
        
        if given_name and user.first_name != given_name:
            user.first_name = given_name
        if family_name and user.last_name != family_name:
            user.last_name = family_name
        
        user.save()
        logger.debug(f"Updated user {user.alias} from ADFS claims")
        
        # Сохраняем claims
        if hasattr(self, 'request'):
            self._save_user_claims(user, claims)
        
        return user

    def get_userinfo_or_id_token(self, access_token, id_token, payload):
        """
        Переопределяем метод для сохранения claims
        """
        user_info = super().get_userinfo_or_id_token(access_token, id_token, payload)

        # Сохраняем полные claims в сессии
        if self.request and hasattr(self.request, 'session'):
            # Сохраняем ID токен
            if id_token:
                self.request.session['oidc_id_token'] = id_token
                self.request.session['oidc_id_token_claims'] = payload

            # Сохраняем access токен
            if access_token:
                self.request.session['oidc_access_token'] = access_token

            # Сохраняем userinfo
            if user_info:
                self.request.session['oidc_userinfo'] = user_info

            logger.debug(f"Saved OIDC data to session")

        return user_info

        return user

    def _save_user_claims(self, user, claims):
        """Сохранение claims в связанной модели профиля"""
        try:
            # Если у вас есть модель Profile, связанная с User
            from .models import UserProfile

            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.oidc_claims = claims  # JSONField
            profile.last_oidc_login = timezone.now()
            profile.save()

            logger.debug(f"Saved OIDC claims for user {user.alias}")
        except ImportError:
            # Модель Profile не существует, сохраняем в сессии
            if hasattr(self, 'request'):
                self.request.session['oidc_user_claims'] = claims

    def verify_token(self, token, **kwargs):
        """
        Верификация токена с логированием
        """
        try:
            result = super().verify_token(token, **kwargs)
            logger.debug(f"Token verification result: {result}")
            return result
        except Exception as e:
            logger.error(f"Token verification failed: {str(e)}")
            raise

    def get_claims(self, token):
        """
        Получение claims из токена
        """
        try:
            # Используем метод из родительского класса
            claims = self.verify_token(token, 'id_token')
            return claims
        except Exception as e:
            logger.error(f"Failed to get claims: {str(e)}")
            return {}

class UsersAuthBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user = Users.objects.get(alias=username)
            # Проверяем пароль (если у вас есть поле password)
            # Если пароля нет в модели, используем другую логику
            # или пропускаем проверку пароля
            return user
        except Users.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return Users.objects.get(id=user_id)
        except Users.DoesNotExist:
            return None


class CustomJWTAuthentication(JWTAuthentication):
    """
    Кастомная JWT аутентификация для модели Users
    """

    def authenticate(self, request):
        """
        Основной метод аутентификации
        """
        header = self.get_header(request)
        if header is None:
            return None

        raw_token = self.get_raw_token(header)
        if raw_token is None:
            return None

        try:
            validated_token = self.get_validated_token(raw_token)
        except Exception as e:
            print(f"[DEBUG AUTH] Token validation error: {e}")
            return None

        user = self.get_user(validated_token)

        if user:
            # Устанавливаем атрибут, чтобы DRF видел пользователя как аутентифицированного
            user._django_user = user  # Для совместимости
            user.backend = 'django.contrib.auth.backends.ModelBackend'

        return user, validated_token

    def get_user(self, validated_token):
        """
        Получает пользователя и добавляет is_manager
        """
        try:
            user_id = validated_token.get('user_id')
            if not user_id:
                return None

            from .models import Users
            user = Users.objects.get(id=user_id)

            # Добавляем is_manager из токена
            user._is_manager_from_token = validated_token.get('is_manager', False)

            print(f"\n[DEBUG AUTH] User {user.alias} loaded")
            print(f"[DEBUG AUTH] Token is_manager: {validated_token.get('is_manager')}")
            print(f"[DEBUG AUTH] Model is_manager property: {user.is_manager}")
            print(f"[DEBUG AUTH] User.is_authenticated: {user.is_authenticated}")

            return user

        except Exception as e:
            print(f"[DEBUG AUTH] Error loading user: {e}")
            return None