from django.contrib.sessions.backends.db import SessionStore as DBSessionStore


class SessionStore(DBSessionStore):
    """
    Session backend, использующий таблицу tsdb_sessions вместо django_session.
    Подключается через SESSION_ENGINE = 'tsdp_backend.session_backend'
    """

    @classmethod
    def get_model_class(cls):
        from .session_model import Session
        return Session
