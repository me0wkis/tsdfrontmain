from mozilla_django_oidc.middleware import SessionRefresh


class CustomSessionRefresh(SessionRefresh):
    """Кастомный middleware для обновления OIDC сессий"""

    def process_request(self, request):
        # Пропускаем API endpoints из обновления сессии
        if request.path.startswith('/api/') and not request.path.startswith('/api/docs/'):
            return

        # Пропускаем health check
        if request.path == '/health/':
            return

        return super().process_request(request)