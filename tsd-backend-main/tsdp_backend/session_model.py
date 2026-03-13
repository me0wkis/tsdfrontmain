from django.contrib.sessions.base_session import AbstractBaseSession


class Session(AbstractBaseSession):
    """
    Кастомная модель сессий — хранится в таблице tsdb_sessions.
    Функционально идентична стандартной django_session.
    """

    class Meta:
        db_table = "tsdb_sessions"
        app_label = "tsdp_backend"
