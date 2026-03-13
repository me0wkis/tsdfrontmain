"""
LDAP аутентификация через прямой bind к AD (без сервисного аккаунта).

Флоу:
  1. Конструируем UPN: username@<LDAP_DOMAIN>
  2. Пытаемся bind к AD-серверу с этими кредами (порт 636, SSL)
  3. Bind успешен → пользователь в AD существует и пароль верен
  4. Далее view проверяет наличие пользователя в таблице Users
"""
import ssl
import logging

from django.conf import settings

logger = logging.getLogger(__name__)


def ldap_authenticate(username: str, password: str) -> tuple[bool, str]:
    """
    Выполняет direct-bind к AD с UPN формата username@domain.

    Возвращает (True, '') при успехе или (False, reason) при ошибке.
    Не бросает исключений наружу.
    """
    try:
        from ldap3 import Server, Connection, Tls
    except ImportError:
        logger.error("ldap3 не установлен. Выполните: pip install ldap3")
        return False, "ldap3 not installed"

    server_host: str = getattr(settings, "LDAP_SERVER", "ru0222dom02.slb.ru")
    port: int = int(getattr(settings, "LDAP_PORT", 636))
    domain: str = getattr(settings, "LDAP_DOMAIN", "slb.ru")

    use_ssl = (port == 636)
    user_upn = f"{username}@{domain}"

    logger.info(f"LDAP: попытка bind как {user_upn} на {server_host}:{port} (ssl={use_ssl})")

    tls_config = None
    if use_ssl:
        # CERT_NONE — корпоративный CA обычно не в системном хранилище.
        # Для включения проверки сертификата переведи LDAP_VERIFY_TLS=True в .env
        # и убедись, что CA-сертификат добавлен в систему.
        verify = ssl.CERT_REQUIRED if getattr(settings, "LDAP_VERIFY_TLS", False) else ssl.CERT_NONE
        tls_config = Tls(validate=verify)

    server = Server(
        server_host,
        port=port,
        use_ssl=use_ssl,
        tls=tls_config,
        connect_timeout=10,
    )

    try:
        conn = Connection(
            server,
            user=user_upn,
            password=password,
            auto_bind=True,        # поднимает исключение если bind не прошёл
            raise_exceptions=True,
        )
        conn.unbind()
        logger.info(f"LDAP: bind успешен для {user_upn}")
        return True, ""
    except Exception as exc:
        logger.warning(f"LDAP: bind не прошёл для {user_upn}: {exc}")
        return False, str(exc)
