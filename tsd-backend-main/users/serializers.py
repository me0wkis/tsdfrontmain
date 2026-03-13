from django.contrib.auth import authenticate
from rest_framework import serializers
from .models import Users, Teams, Desks

class TeamsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Teams
        fields = ['id','team_name','team_color']

class DesksSerializer(serializers.ModelSerializer):
    class Meta:
        model = Desks
        fields = ['id','desk_number']

class CategoryFilterSerializer(serializers.Serializer):
    """Сериализатор для фильтрации по категориям"""
    category_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        help_text="Список ID категорий для фильтрации (если не указан - фильтрация не применяется)"
    )
    category_names = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text="Список названий категорий для фильтрации"
    )
    include_without_category = serializers.BooleanField(
        required=False,
        default=False,
        help_text="Включать ли пользователей без категории (usercategories_id IS NULL)"
    )


class SyncRequestSerializer(serializers.Serializer):
    """Сериализатор для параметров запроса"""
    source_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        help_text="Список ID записей для синхронизации (если не указан - синхронизируются все)"
    )
    category_filter = CategoryFilterSerializer(
        required=False,
        help_text="Фильтр по категориям пользователей"
    )
    dry_run = serializers.BooleanField(
        required=False,
        default=False,
        help_text="Если true - только подсчет записей без реальной вставки"
    )
    batch_size = serializers.IntegerField(
        required=False,
        default=1000,
        help_text="Размер пакета для массовой вставки"
    )

class SyncStatisticsSerializer(serializers.Serializer):
    """Сериализатор для статистики синхронизации"""
    processed = serializers.IntegerField(help_text="Всего обработано записей")
    filtered_out = serializers.IntegerField(help_text="Отфильтровано (не подходят по категории)")
    new = serializers.IntegerField(help_text="Добавлено новых записей")
    skipped = serializers.IntegerField(help_text="Пропущено (уже существовали)")
    errors = serializers.IntegerField(help_text="Ошибок при обработке")
    details = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        help_text="Детализация по каждой записи"
    )

class SyncResponseSerializer(serializers.Serializer):
    """Сериализатор для ответа"""
    status = serializers.CharField(help_text="Статус операции (success/error)")
    message = serializers.CharField(help_text="Сообщение о результате")
    statistics = SyncStatisticsSerializer(required=False, help_text="Статистика синхронизации")
    applied_filters = serializers.DictField(required=False, help_text="Примененные фильтры")

class UsersWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Users
        fields = ['id',
                    'alias',
                    'first_name',
                    'second_name',
                    'job_title',
                    'group_name',
                    'hiring_date',
                    'supervisor_name',
                    'email',
                    'phone_number',
                    'desk',
                    'team',
                    'avatar_url',
                    'cc_abonent_id',
                    'is_active'
        ]

class UsersReadSerializer(serializers.ModelSerializer):
    desk = serializers.CharField(source='desk.desk_number')
    team = serializers.CharField(source='team.team_name')
    class Meta:
        model = Users
        fields = ['id',
                    'alias',
                    'first_name',
                    'second_name',
                    'job_title',
                    'group_name',
                    'hiring_date',
                    'supervisor_name',
                    'email',
                    'phone_number',
                    'desk',
                    'team',
                    'avatar_url',
                    'cc_abonent_id',
                    'is_active'
        ]


class UserLoginSerializer(serializers.Serializer):
    email = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')

        if not email:
            raise serializers.ValidationError('Email is required')

        try:
            user = Users.objects.get(email=email, is_active=1)
            data['user'] = user
            return data
        except Users.DoesNotExist:
            raise serializers.ValidationError('User not found or inactive')

class LoginInputSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, style={'input_type': 'password'})

class RefreshTokenSerializer(serializers.Serializer):
    refresh = serializers.CharField(required=True)

class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField(required=True)