from django.urls import reverse
from drf_yasg.inspectors import SwaggerAutoSchema


class OIDCSwaggerSchema(SwaggerAutoSchema):
    """Кастомная схема Swagger с OIDC авторизацией"""

    def get_security_definitions(self):
        security_defs = super().get_security_definitions() or {}

        # Добавляем OIDC security scheme
        security_defs['OIDC'] = {
            'type': 'oauth2',
            'flow': 'implicit',
            'authorizationUrl': reverse('oidc_authentication_init'),
            'scopes': {
                'openid': 'OpenID scope',
                'email': 'Email access',
                'profile': 'Profile access',
            }
        }

        return security_defs

    def get_security_requirements(self):
        # Требуем аутентификацию для всех endpoints
        return [{'OIDC': ['openid', 'email', 'profile']}]

