import json
import logging
import re
import secrets
import traceback
from typing import Any

import requests
from django.db import transaction, connections
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt
from mozilla_django_oidc.utils import import_from_settings

from .utils import create_jwt_token
from django.db.models import Q
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.http import HttpResponseRedirect, JsonResponse
from django.contrib.auth import logout as django_logout
from mozilla_django_oidc.views import OIDCLogoutView, OIDCAuthenticationCallbackView
from django.conf import settings
from urllib.parse import urlencode
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
import jwt
import logging

from .models import Users, Teams, Desks, GLPICategory, GLPIUsers, GLPITitle, GLPIGroupsUsers, GLPIGroups
from .serializers import UsersReadSerializer, UsersWriteSerializer, TeamsSerializer, DesksSerializer, \
    UserLoginSerializer, RefreshTokenSerializer, LogoutSerializer, LoginInputSerializer, SyncRequestSerializer, \
    SyncResponseSerializer
from .ldap_auth import ldap_authenticate
from .oidc_views import _create_session, SESSION_COOKIE_NAME, SESSION_TIMEOUT
from django_filters import rest_framework as filters
from rest_framework import generics, status, request
from .pagination import CustomLimitOffsetPagination
from .permissions import IsManager

class UsersListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsManager]
    queryset = Users.objects.select_related('team').all()

    def get_serializer_class(self):  # type: ignore[override]
        if self.request.method == 'GET':
            return UsersReadSerializer
        return UsersWriteSerializer
    pagination_class = CustomLimitOffsetPagination
    filter_backends = [filters.DjangoFilterBackend]

    def get_queryset(self):
        queryset = super().get_queryset()
        filter_param = self.request.GET.get('filter')
        if filter_param:
            try:
                filter_list = json.loads(filter_param)
                if isinstance(filter_list, list):
                    queryset = self.apply_filters(queryset, filter_list)
            except json.JSONDecodeError:
                if isinstance(filter_param, str):
                    queryset = self.apply_filters(queryset, [filter_param])
        sort_param = self.request.GET.get('sort')
        if sort_param:
            try:
                sort_list = json.loads(sort_param)
                if isinstance(sort_list, list):
                    queryset = self.apply_sorting(queryset, sort_list)
            except json.JSONDecodeError:
                if isinstance(sort_param, str):
                    queryset = self.apply_sorting(queryset, [sort_param])

        return queryset

    def apply_filters(self, queryset, filter_list):
        q_objects = Q()

        for filter_str in filter_list:
            if not isinstance(filter_str, str):
                continue

            match = re.match(r'^([a-zA-Z0-9_]+)-([a-zA-Z]+)-(.+)$', filter_str)
            if not match:
                continue

            field, operator, value = match.groups()
            if field in ['team__name', 'team__team_name', 'team_name']:
                try:
                    team = Teams.objects.get(team_name=value)
                    field = 'team'
                    value = team.id
                except Teams.DoesNotExist:
                    return Users.objects.none()
                except Teams.MultipleObjectsReturned:
                    team = Teams.objects.filter(team_name=value).first()
                    field = 'team'
                    value = team.id if team else None

            elif field in ['desk__number', 'desk_number']:
                try:
                    desk = Desks.objects.get(number=value)
                    field = 'desk'
                    value = desk.id
                except Desks.DoesNotExist:
                    return Users.objects.none()
                except Desks.MultipleObjectsReturned:
                    desk = Desks.objects.filter(number=value).first()
                    field = 'desk'
                    value = desk.id if desk else None

            operator_map = {
                'eq': 'exact',
                'ne': 'ne',
                'gt': 'gt',
                'gte': 'gte',
                'lt': 'lt',
                'lte': 'lte',
                'contains': 'icontains',
                'startswith': 'istartswith',
                'endswith': 'iendswith',
            }

            if operator not in operator_map:
                continue

            lookup = f"{field}__{operator_map[operator]}"

            try:
                if '__' in field:
                    pass
                elif operator in ['eq', 'ne', 'gt', 'gte', 'lt', 'lte']:
                    if value is not None:
                        if field in ['is_active']:
                            value = bool(int(value))
                        else:
                            value = int(value)
            except (ValueError, TypeError):
                pass

            if operator == 'ne':
                q_objects &= ~Q(**{lookup.replace('__ne', ''): value})
            else:
                q_objects &= Q(**{lookup: value})

        return queryset.filter(q_objects)

    def apply_sorting(self, queryset, sort_input):
        """Применяет сортировку, поддерживая разные форматы"""
        order_by = []
        if isinstance(sort_input, list):
            sort_list = sort_input
        elif isinstance(sort_input, str):
            try:
                sort_list = json.loads(sort_input)
                if not isinstance(sort_list, list):
                    sort_list = [sort_input]
            except json.JSONDecodeError:
                sort_list = [sort_input]
        else:
            sort_list = []

        for sort_str in sort_list:
            if not isinstance(sort_str, str):
                continue

            match = re.match(r'^([a-zA-Z0-9_]+)-(asc|desc)$', sort_str)
            if match:
                field, order = match.groups()
                order_by.append(f'-{field}' if order == 'desc' else field)
            else:
                order_by.append(sort_str)

        if order_by:
            return queryset.order_by(*order_by)

        return queryset

    @extend_schema(
        summary="Get list of users with advanced filtering",
        description="""
    ## Advanced Filtering System

    Use the `filter` parameter with format: **field-operator-value**

    ### Examples:
    - `filter=first_name-eq-John` - First name equals "John"
    - `filter=is_active-eq-1` - Is active equals 1
    - `filter=hiring_date-gt-2023-01-01` - Hiring date after 2023-01-01

    ### Multiple Filters:
    Add multiple `filter` parameters:
    `filter=first_name-eq-John&filter=is_active-eq-1&filter=hiring_date-gt-2023-01-01`

    ### Available Operators:
    | Operator | Description | Example |
    |----------|-------------|---------|
    | `eq` | Equals | `first_name-eq-John` |
    | `ne` | Not equals | `is_active-ne-0` |
    | `gt` | Greater than | `hiring_date-gt-2023-01-01` |
    | `lt` | Less than | `hiring_date-lt-2024-01-01` |
    | `contains` | Contains | `job_title-contains-manager` |

    ### Available Fields:
    - `first_name`, `second_name`, `alias`, `email`
    - `job_title`, `is_active`, `hiring_date`, `group_name`
    - `supervisor_name`, `team__name`, `desk__number`
            """,
        parameters=[
            OpenApiParameter(
                name='filter',
                description='''
    Filter parameters in format: field-operator-value

    **Examples:**
    - first_name-eq-John
    - is_active-eq-1
    - hiring_date-gt-2023-01-01

    **Multiple filters:** Use multiple filter parameters
    
    **Note:** Use `__` for related fields, not single `_`
                    ''',
                required=False,
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                style='form',
                explode=True
            ),
            OpenApiParameter(
                name='sort',
                description='Sort parameters in format: field-order (asc/desc)',
                required=False,
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                style='form',
                explode=True
            ),
            OpenApiParameter(
                name='limit',
                description='Number of results per page',
                required=False,
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY
            ),
            OpenApiParameter(
                name='offset',
                description='Pagination offset',
                required=False,
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY
            )
        ],
        examples=[
            OpenApiExample(
                'Filter by name and active status',
                value={},
                description='Example: ?filter=first_name-eq-John&filter=is_active-eq-1',
            ),
            OpenApiExample(
                'Sort by date and paginate',
                value={},
                description='Example: ?sort=hiring_date-desc&limit=10&offset=20',
            )
        ]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class SyncEmployeeDataView(APIView):
    """
    API endpoint для синхронизации данных сотрудников с фильтрацией по категориям.

    Переносит данные из исходной таблицы в целевую с подстановкой
    названий должностей вместо ID.
    Запись происходит только для пользователей, подходящих под фильтр категорий,
    и только если пользователь с таким ID отсутствует в целевой таблице.
    """

    permission_classes = [AllowAny]
    authentication_classes = []
    TRACKED_FIELDS = ['job_title', 'group_name', 'second_name', 'supervisor_name', 'phone_number']

    @extend_schema(
        summary="Синхронизировать данные сотрудников",
        description="""
            Переносит данные из исходной таблицы в целевую с подстановкой названий должностей вместо ID.

            **Как это работает:**
            1. Фильтрация записей по указанным категориям
            2. Проверка существования записи в целевой таблице
            3. Добавление только новых записей
            4. Подстановка названия должности вместо ID

            **Примеры использования:**
            - `/api/sync-employees/?category_ids=1,2,3` - синхронизация категорий 1,2,3
            - `/api/sync-employees/?category_names=Manager,Developer&dry_run=true` - тестовый прогон
            - `/api/sync-employees/?source_ids=101,102,103&include_without_category=true` - конкретные ID
            """,
        parameters=[
            OpenApiParameter(
                name='category_ids',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
                description='ID категорий через запятую (например: 1,2,3)',
                examples=[
                    OpenApiExample(
                        'Пример 1',
                        value='1,2,3',
                        description='Синхронизация категорий 1, 2 и 3'
                    ),
                    OpenApiExample(
                        'Пример 2',
                        value='5,7,10',
                        description='Синхронизация категорий 5, 7 и 10'
                    ),
                ]
            ),
            OpenApiParameter(
                name='category_names',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
                description='Названия категорий через запятую (например: Manager,Developer)',
                examples=[
                    OpenApiExample(
                        'Пример 1',
                        value='Manager,Developer',
                        description='Синхронизация категорий с названиями Manager и Developer'
                    ),
                ]
            ),
            OpenApiParameter(
                name='include_without_category',
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                required=False,
                default=False,
                description='Включать пользователей без категории (usercategories_id IS NULL)',
                examples=[
                    OpenApiExample(
                        'Пример',
                        value='true',
                        description='Включить пользователей без категории'
                    ),
                ]
            ),
            OpenApiParameter(
                name='source_ids',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
                description='ID записей для синхронизации через запятую',
                examples=[
                    OpenApiExample(
                        'Пример',
                        value='101,102,103',
                        description='Синхронизация только записей с ID 101, 102 и 103'
                    ),
                ]
            ),
            OpenApiParameter(
                name='dry_run',
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                required=False,
                default=False,
                description='Только подсчет без реальной вставки (для проверки)',
                examples=[
                    OpenApiExample(
                        'Пример',
                        value='true',
                        description='Тестовый прогон без изменений в БД'
                    ),
                ]
            ),
            OpenApiParameter(
                name='batch_size',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                required=False,
                default=1000,
                description='Размер пакета для массовой вставки (макс. 10000)',
                examples=[
                    OpenApiExample(
                        'Пример',
                        value='500',
                        description='Вставлять по 500 записей за раз'
                    ),
                ]
            ),
            OpenApiParameter(
                name='format',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
                enum=['json', 'csv'],
                description='Формат ответа (json или csv)',
                default='json',
            ),
        ],
        responses={
            200: OpenApiTypes.OBJECT,
            400: OpenApiTypes.OBJECT,
            500: OpenApiTypes.OBJECT,
        },
        examples=[
            OpenApiExample(
                'Успешный ответ',
                value={
                    'status': 'success',
                    'message': 'Sync completed successfully',
                    'statistics': {
                        'processed': 150,
                        'new': 45,
                        'skipped': 105,
                        'errors': 0
                    },
                    'applied_filters': {
                        'category_ids': [1, 2, 3],
                        'include_without_category': False
                    }
                },
                response_only=True,
            ),
            OpenApiExample(
                'Тестовый прогон',
                value={
                    'status': 'success',
                    'message': 'Dry run completed',
                    'statistics': {
                        'processed': 150,
                        'new': 45,
                        'skipped': 105,
                        'errors': 0,
                        'details': [
                            {'id': 101, 'action': 'will_create', 'category_id': 1},
                            {'id': 102, 'action': 'skipped', 'reason': 'already_exists', 'category_id': 2},
                        ]
                    },
                    'applied_filters': {
                        'category_ids': [1, 2, 3]
                    }
                },
                response_only=True,
            ),
        ],
        tags=['Analytics sync'],
    )
    def get(self, request):
        try:
            params = self._parse_params(request)

            result = self._execute_sync(params)

            return Response({
                'status': 'success',
                'message': 'Dry run completed' if params['dry_run'] else 'Sync completed successfully',
                'statistics': result['statistics'],
                'applied_filters': result['applied_filters']
            })

        except ValueError as e:
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Sync failed: {str(e)}", exc_info=True)
            return Response(
                {'status': 'error', 'message': f'Internal server error: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _parse_params(self, request):
        """Парсинг параметров из запроса"""
        params = {
            'category_ids': [],
            'category_names': [],
            'include_without_category': False,
            'source_ids': [],
            'dry_run': False,
            'force_update': False
        }

        category_ids_str = request.query_params.get('category_ids', '')
        if category_ids_str:
            try:
                params['category_ids'] = [int(id.strip()) for id in category_ids_str.split(',') if id.strip()]
            except ValueError:
                raise ValueError("category_ids должны быть числами")

        category_names_str = request.query_params.get('category_names', '')
        if category_names_str:
            params['category_names'] = [name.strip() for name in category_names_str.split(',') if name.strip()]

        include_without = request.query_params.get('include_without_category', 'false').lower()
        params['include_without_category'] = include_without in ['true', '1', 'yes']

        source_ids_str = request.query_params.get('source_ids', '')
        if source_ids_str:
            try:
                params['source_ids'] = [int(id.strip()) for id in source_ids_str.split(',') if id.strip()]
            except ValueError:
                raise ValueError("source_ids должны быть числами")

        dry_run = request.query_params.get('dry_run', 'false').lower()
        params['dry_run'] = dry_run in ['true', '1', 'yes']
        force_update = request.query_params.get('force_update', 'false').lower()
        params['force_update'] = force_update in ['true', '1', 'yes']

        return params

    def _execute_sync(self, params):
        """Выполнение синхронизации"""
        logger.info(f"Starting sync with params: {params}")

        queryset = GLPIUsers.objects.using('second_db').all()

        if params['source_ids']:
            queryset = queryset.filter(id__in=params['source_ids'])

        if params['category_ids'] or params['category_names'] or params['include_without_category']:
            queryset = self._apply_category_filters(queryset, params)

        all_users = list(queryset)
        logger.info(f"Found {len(all_users)} records")

        if not all_users:
            return {
                'statistics': {
                    'processed': 0,
                    'new': 0,
                    'skipped': 0,
                    'errors': 0
                },
                'applied_filters': params
            }

        user_ids = [u.id for u in all_users]

        user_groups = self._get_user_groups(user_ids)

        supervisors_cache = self._build_supervisors_cache(all_users)

        existing_records = {
            r.id: r for r in Users.objects.using('default').filter(
                id__in=user_ids
            )
        }
        logger.info(f"Found {len(existing_records)} existing records in destination")

        stats = {
            'processed': len(all_users),
            'new': 0,
            'updated': 0,
            'skipped': 0,
            'errors': 0,
            'details': [] if params['dry_run'] else None
        }

        new_records = []
        update_records = []

        for user in all_users:
            try:
                job_title = self._get_job_title(user)
                group_name = user_groups.get(user.id)
                supervisor_name = self._get_supervisor_name(user, supervisors_cache)
                email = self._build_email(user)

                user_data = {
                    'id': user.id,
                    'alias': getattr(user, 'alias', '') or '',
                    'first_name': getattr(user, 'first_name', '') or '',
                    'second_name': getattr(user, 'second_name', '') or '',
                    'job_title': job_title or '',
                    'group_name': group_name or '',
                    'hiring_date': getattr(user, 'hiring_date', None),
                    'supervisor_name': supervisor_name or '',
                    'email': email or '',
                    'phone_number': getattr(user, 'phone_number', '') or '',
                    'desk_id': getattr(user, 'desk_id', None),
                    'team_id': getattr(user, 'team_id', None),
                    'avatar_url': getattr(user, 'avatar_url', '') or '',
                    'cc_abonent_id': getattr(user, 'cc_abonent_id', '') or '',
                    'is_active': bool(getattr(user, 'is_active', True))
                }

                if user.id in existing_records:
                    existing = existing_records[user.id]

                    changes, changed_fields = self._get_changed_fields(existing, user_data)

                    if not changes or params['force_update']:
                        if params['force_update']:
                            stats['updated'] += 1
                            action = 'force_updated'
                            if params['dry_run']:
                                stats['details'].append({
                                    'id': user.id,
                                    'action': 'would_force_update',
                                    'changed_fields': self.TRACKED_FIELDS
                                })
                            else:
                                for field in self.TRACKED_FIELDS:
                                    setattr(existing, field, user_data[field])
                                update_records.append(existing)
                        else:
                            stats['skipped'] += 1
                            if params['dry_run']:
                                stats['details'].append({
                                    'id': user.id,
                                    'action': 'skipped',
                                    'reason': 'no_changes'
                                })
                    else:
                        stats['updated'] += 1
                        if params['dry_run']:
                            stats['details'].append({
                                'id': user.id,
                                'action': 'would_update',
                                'changed_fields': changed_fields,
                                'changes': changes
                            })
                        else:
                            for field, value in changes.items():
                                setattr(existing, field, value)
                            update_records.append(existing)
                else:
                    stats['new'] += 1
                    if not params['dry_run']:
                        new_records.append(Users(**user_data))

                    if params['dry_run']:
                        stats['details'].append({
                            'id': user.id,
                            'action': 'would_create',
                            'data': {k: v for k, v in user_data.items() if k in self.TRACKED_FIELDS}
                        })

                if not params['dry_run']:
                    if len(new_records) >= 1000:
                        Users.objects.using('default').bulk_create(new_records)
                        logger.info(f"Bulk created {len(new_records)} records")
                        new_records = []

                    if len(update_records) >= 1000:
                        Users.objects.using('default').bulk_update(
                            update_records, self.TRACKED_FIELDS
                        )
                        logger.info(f"Bulk updated {len(update_records)} records")
                        update_records = []

            except Exception as e:
                stats['errors'] += 1
                logger.error(f"Error processing user {user.id}: {str(e)}", exc_info=True)
                if params['dry_run']:
                    stats['details'].append({
                        'id': user.id,
                        'action': 'error',
                        'error': str(e)
                    })

        if not params['dry_run']:
            if new_records:
                Users.objects.using('default').bulk_create(new_records)
                logger.info(f"Final bulk created {len(new_records)} records")

            if update_records:
                Users.objects.using('default').bulk_update(
                    update_records, self.TRACKED_FIELDS
                )
                logger.info(f"Final bulk updated {len(update_records)} records")

        logger.info(f"Sync completed. Stats: {stats}")

        return {
            'statistics': stats,
            'applied_filters': params
        }

    def _apply_category_filters(self, queryset, params):
        """Применение фильтров по категориям"""
        conditions = Q()

        if params['category_ids']:
            conditions |= Q(usercategories_id__in=params['category_ids'])

        if params['category_names']:
            category_ids = []
            for name in params['category_names']:
                try:
                    cats = GLPICategory.objects.using('second_db').filter(name__icontains=name)
                    category_ids.extend([c.id for c in cats])
                except Exception as e:
                    logger.error(f"Error finding category {name}: {str(e)}")

            if category_ids:
                conditions |= Q(usercategories_id__in=category_ids)

        if params['include_without_category']:
            conditions |= Q(usercategories_id__isnull=True)

        if conditions:
            queryset = queryset.filter(conditions)

        return queryset

    def _get_user_groups(self, user_ids):
        """
        Получение групп для пользователей из groups_users и groups
        Возвращает словарь {user_id: group_name}
        """
        logger.info(f"Getting groups for {len(user_ids)} users")

        user_groups = GLPIGroupsUsers.objects.using('second_db').filter(
            user_id__in=user_ids
        )

        group_ids = set(ug.group_id for ug in user_groups)

        groups_dict = {}
        if group_ids:
            groups = GLPIGroups.objects.using('second_db').filter(id__in=group_ids)
            groups_dict = {g.id: g.name for g in groups}

        result = {}
        for ug in user_groups:
            if ug.user_id not in result:
                result[ug.user_id] = groups_dict.get(ug.group_id)

        logger.info(f"Found groups for {len(result)} users")
        return result

    def _get_job_title(self, user):
        """Получение названия должности"""
        try:
            if hasattr(user, 'user_title') and user.user_title:
                if hasattr(user.user_title, 'name'):
                    return user.user_title.name
                elif hasattr(user.user_title, 'title'):
                    return user.user_title.title
        except:
            pass
        return getattr(user, 'job_title', None)

    def _get_supervisor_name(self, user, supervisors_cache=None):
        """
        Получение имени руководителя по ID
        supervisor_name в модели SourceUsers - это ID руководителя (users_id_supervisor)
        """
        try:
            supervisor_id = getattr(user, 'supervisor_name', None)
            if supervisor_id:
                if supervisors_cache and supervisor_id in supervisors_cache:
                    return supervisors_cache[supervisor_id]
                supervisor = GLPIUsers.objects.using('second_db').filter(id=supervisor_id).first()
                if supervisor:
                    alias = getattr(supervisor, 'alias', '')
                    return alias

        except Exception as e:
            logger.warning(f"Error getting supervisor name for user {getattr(user, 'id', None)}: {str(e)}")

        return None

    def _build_supervisors_cache(self, users):
        """
        Создание кэша руководителей для оптимизации
        """
        supervisor_ids = set()
        for user in users:
            sup_id = getattr(user, 'supervisor_name', None)
            if sup_id:
                supervisor_ids.add(sup_id)

        cache = {}
        if supervisor_ids:
            supervisors = GLPIUsers.objects.using('second_db').filter(
                id__in=supervisor_ids
            ).only('id', 'alias')

            for sup in supervisors:
                alias = getattr(sup, 'alias', '')
                cache[sup.id] = alias
        return cache

    def _build_email(self, user):
        """Формирование email из alias"""
        alias = getattr(user, 'alias', '')
        if alias:
            return f"{alias}@slb.ru"
        return None

    def _compare_field_values(self, old_value, new_value):
        """
        Сравнение значений полей с обработкой None
        """
        if old_value is None and new_value is None:
            return True
        if old_value is None or new_value is None:
            return False
        return str(old_value).strip() == str(new_value).strip()

    def _get_changed_fields(self, existing_record, new_data):
        """
        Определение полей, которые изменились
        Возвращает словарь с изменениями и список измененных полей
        """
        changes = {}
        changed_fields = []

        for field in self.TRACKED_FIELDS:
            old_value = getattr(existing_record, field, None)
            new_value = new_data.get(field)

            if not self._compare_field_values(old_value, new_value):
                changes[field] = new_value
                changed_fields.append(field)
                logger.debug(f"Field {field} changed: '{old_value}' -> '{new_value}'")

        return changes, changed_fields

    def _get_supervisor_name_batch(self, users):
        """
        Оптимизированное получение имен руководителей для списка пользователей
        """
        supervisor_ids = set()
        for user in users:
            supervisor_id = getattr(user, 'supervisor_name', None)
            if supervisor_id:
                supervisor_ids.add(supervisor_id)

        supervisors = {}
        if supervisor_ids:
            supervisor_users = GLPIUsers.objects.using('second_db').filter(
                id__in=supervisor_ids
            ).only('id', 'first_name', 'second_name', 'alias')

            for sup in supervisor_users:
                first_name = getattr(sup, 'first_name', '')
                second_name = getattr(sup, 'second_name', '')
                if first_name and second_name:
                    supervisors[sup.id] = f"{first_name} {second_name}"
                elif first_name:
                    supervisors[sup.id] = first_name
                elif second_name:
                    supervisors[sup.id] = second_name
                else:
                    supervisors[sup.id] = getattr(sup, 'alias', '')

        return supervisors

class UsersRetrieveView(generics.RetrieveAPIView):
    permission_classes = [IsManager]

    def post(self, request):
        print(f"User: {request.user.first_name}, Job: {request.user.job_title}, IsManager: {request.user.is_manager}")

        if not request.user.is_manager:
            return Response(
                "Only managers can perform shift exchanges",
                status=status.HTTP_403_FORBIDDEN
            )
    queryset = Users.objects.select_related('team', 'desk').all()
    serializer_class = UsersReadSerializer

@extend_schema(operation_id='users_update')
class UsersUpdateView(generics.UpdateAPIView):
    permission_classes = [IsManager]
    queryset = Users.objects.all()
    serializer_class = UsersWriteSerializer

@extend_schema(operation_id='users_delete')
class UsersDestroyView(generics.DestroyAPIView):
    permission_classes = [IsManager]
    queryset = Users.objects.all()
    serializer_class = UsersWriteSerializer

class TeamsListCreateView(generics.ListCreateAPIView):
    """Создание и просмотр команд"""
    permission_classes = [IsManager]

    def post(self, request):
        print(f"User: {request.user.first_name}, Job: {request.user.job_title}, IsManager: {request.user.is_manager}")

        if not request.user.is_manager:
            return Response(
                "Only managers can perform shift exchanges",
                status=status.HTTP_403_FORBIDDEN
            )
        return super().post(request)
    queryset = Teams.objects.all()
    pagination_class = CustomLimitOffsetPagination
    serializer_class = TeamsSerializer

@extend_schema(operation_id='teams_detail')
class TeamsRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """CRUD для команд"""
    permission_classes = [IsManager]
    queryset = Teams.objects.all()
    serializer_class = TeamsSerializer

class DesksListCreateView(generics.ListCreateAPIView):
    """Создание и просмотр рабочих мест"""
    permission_classes = [IsManager]

    def post(self, request):
        print(f"User: {request.user.first_name}, Job: {request.user.job_title}, IsManager: {request.user.is_manager}")

        if not request.user.is_manager:
            return Response(
                "Only managers can perform shift exchanges",
                status=status.HTTP_403_FORBIDDEN
            )
        return super().post(request)
    queryset = Desks.objects.all()
    pagination_class = CustomLimitOffsetPagination
    serializer_class = DesksSerializer

@extend_schema(operation_id='desks_detail')
class DesksRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """CRUD для рабочих мест"""
    permission_classes = [IsManager]
    queryset = Desks.objects.all()
    serializer_class = DesksSerializer


class LoginView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="User login",
        description="[LEGACY] JWT авторизация по email. Не используется — текущая авторизация через ADFS (/auth/login).",
        deprecated=True,
        request={
            'application/json': {
                'type': 'object',
                'required': ['email'],
                'properties': {
                    'email': {'type': 'string', 'example': 'user@company.com'},
                    'password': {'type': 'string', 'example': 'any_value'},
                }
            }
        },
        responses={
            200: openapi.Response('Success'),
            400: openapi.Response('Bad Request')
        }
    )
    def post(self, request):
        email = request.data.get('email')

        if not email:
            return Response({
                'error': 'Email is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = Users.objects.get(email=email, is_active=1)

            # Используем нашу кастомную функцию
            tokens = create_jwt_token(user)

            return Response({
                'refresh': tokens['refresh'],
                'access': tokens['access'],
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'first_name': user.first_name,
                    'second_name': user.second_name,
                    'job_title': user.job_title,
                    'is_manager': user.is_manager
                }
            })

        except Users.DoesNotExist:
            return Response({
                'error': 'User not found or inactive'
            }, status=status.HTTP_400_BAD_REQUEST)


class LDAPLoginView(APIView):
    """
    POST /api/portal/auth/ldap/
    Аутентификация по логину/паролю через корпоративный AD (LDAPS, порт 636).
    Пользователь должен существовать в таблице Users — иначе вход запрещён.
    При успехе устанавливает session_token cookie (аналогично OIDC-флоу).
    """
    permission_classes = [AllowAny]

    @extend_schema(
        summary="LDAP login (AD)",
        description=(
            "Аутентификация через корпоративный Active Directory (LDAPS).\n\n"
            "Требования:\n"
            "- Пользователь должен быть заведён в таблице `users` (поле `alias`).\n"
            "- Пароль проверяется напрямую в AD (direct user bind).\n\n"
            "При успехе устанавливает cookie `session_token`, который используется "
            "всеми остальными эндпоинтами."
        ),
        request={
            'application/json': {
                'type': 'object',
                'required': ['username', 'password'],
                'properties': {
                    'username': {'type': 'string', 'example': 'ivanov'},
                    'password': {'type': 'string', 'example': 'secret'},
                },
            }
        },
        responses={
            200: openapi.Response('Authenticated — session_token cookie выставлен'),
            400: openapi.Response('Не указан username или password'),
            401: openapi.Response('Неверные учётные данные или пользователь не найден в БД'),
        },
    )
    def post(self, request):
        raw_username = (request.data.get('username') or '').strip()
        password = request.data.get('password') or ''

        if not raw_username or not password:
            return Response(
                {'error': 'username and password are required'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Отрезаем @domain, если пользователь ввёл полный UPN (например, user@slb.ru)
        username = raw_username.split('@')[0] if '@' in raw_username else raw_username

        # Шаг 1: проверка пароля в Active Directory
        ok, reason = ldap_authenticate(username, password)
        if not ok:
            logger.warning(f"LDAP login failed for username='{username}' (raw='{raw_username}'): {reason}")
            return Response(
                {'error': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Шаг 2: пользователь обязан быть в нашей БД
        try:
            db_user = Users.objects.get(alias__iexact=username, is_active=1)
        except Users.DoesNotExist:
            # Диагностика: ищем без фильтра is_active, чтобы понять причину
            any_user = Users.objects.filter(alias__iexact=username).first()
            if any_user:
                logger.warning(
                    f"LDAP: '{username}' найден в БД (id={any_user.id}), "
                    f"но is_active={any_user.is_active} — вход запрещён"
                )
            else:
                logger.warning(
                    f"LDAP: '{username}' прошёл AD, но не найден в таблице users. "
                    f"Проверьте поле alias: запрос был alias__iexact='{username}'"
                )
            return Response(
                {'error': 'Access denied. Contact your administrator.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Шаг 3: создаём сессию через тот же механизм, что и OIDC
        session_payload = {
            'id': db_user.id,
            'alias': db_user.alias,
            'email': db_user.email,
            'first_name': db_user.first_name,
            'second_name': db_user.second_name,
            'job_title': db_user.job_title,
            'is_manager': db_user.is_manager,
        }
        session_token = _create_session(session_payload)

        response = Response({'user': session_payload}, status=status.HTTP_200_OK)
        response.set_cookie(
            key=SESSION_COOKIE_NAME,
            value=session_token,
            httponly=True,
            secure=True,
            samesite=getattr(settings, 'COOKIE_SAMESITE', 'Lax'),
            max_age=SESSION_TIMEOUT,
        )
        logger.info(f"LDAP login successful for '{db_user.alias}'")
        return response


class RefreshTokenView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Refresh JWT token",
        description="[LEGACY] Обновление JWT access токена. Не используется с OIDC авторизацией.",
        deprecated=True,
    )
    @swagger_auto_schema(
        operation_description="Refresh access token using refresh token",
        request_body=RefreshTokenSerializer,
        responses={
            200: openapi.Response(
                description="Token refreshed successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'access': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                )
            )
        }
    )

    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response({'error': 'Refresh token is required'}, status=400)

        try:
            refresh = RefreshToken(refresh_token)
            access_token = str(refresh.access_token)
            return Response({'access': access_token})
        except Exception as e:
            return Response({'error': 'Invalid refresh token'}, status=400)


class LogoutView(APIView):
    @extend_schema(
        summary="JWT Logout",
        description="[LEGACY] Инвалидация refresh токена. Не используется — выход через /auth/logout.",
        deprecated=True,
    )
    @swagger_auto_schema(
        operation_description="Logout user and blacklist refresh token",
        request_body=LogoutSerializer,
        responses={
            200: openapi.Response(
                description="Logout successful",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                )
            )
        }
    )
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'message': 'Successfully logged out'})
        except Exception as e:
            return Response({'error': 'Invalid token'}, status=400)

logger = logging.getLogger(__name__)

class CustomOIDCLogoutView(OIDCLogoutView):
    """Кастомный логаут с редиректом на провайдера OIDC"""

    def get(self, request):
        # Получаем токены из сессии
        id_token = request.session.get('oidc_id_token')
        django_logout(request)

        # Очищаем сессию
        if 'oidc_id_token' in request.session:
            del request.session['oidc_id_token']
        if 'oidc_access_token' in request.session:
            del request.session['oidc_access_token']
        if 'oidc_refresh_token' in request.session:
            del request.session['oidc_refresh_token']

        # Если настроен endpoint логаута провайдера
        if hasattr(settings, 'OIDC_OP_LOGOUT_ENDPOINT') and settings.OIDC_OP_LOGOUT_ENDPOINT:
            # Строим URL для логаута у провайдера
            logout_url = settings.OIDC_OP_LOGOUT_ENDPOINT
            params = {
                'post_logout_redirect_uri': request.build_absolute_uri(settings.LOGOUT_REDIRECT_URL),
            }

            if id_token:
                params['id_token_hint'] = id_token

            full_logout_url = f"{logout_url}?{urlencode(params)}"
            logger.info(f"Redirecting to OIDC logout: {full_logout_url}")
            return HttpResponseRedirect(full_logout_url)

        return HttpResponseRedirect(settings.LOGOUT_REDIRECT_URL)


def health_check(request):
    """Health check endpoint для проверки работы сервиса"""
    from django.http import JsonResponse
    return JsonResponse({'status': 'ok', 'service': 'django-oidc'})


@method_decorator(csrf_exempt, name='dispatch')
class SimplePostCallbackView(APIView):

    def post(self, request):
        # Получаем код из POST данных
        code = request.POST.get('code')

        if not code:
            return JsonResponse({'error': 'No code provided'}, status=400)

        # Обмениваем код на токен
        token_response = requests.post(
            'https://your-oidc-provider.com/token',
            data={
                'grant_type': 'authorization_code',
                'code': code,
                'client_id': 'your-client-id',
                'client_secret': 'your-secret',
                'redirect_uri': 'https://your-portal.com/callback/'
            }
        )

        if token_response.status_code == 200:
            tokens = token_response.json()
            # Здесь логика создания/аутентификации пользователя
            return JsonResponse({'success': True, 'tokens': tokens})
        else:
            return JsonResponse({'error': 'Token exchange failed'}, status=400)

@method_decorator(csrf_exempt, name='dispatch')  # Важно: отключаем CSRF для callback
class PostOIDCCallbackView(OIDCAuthenticationCallbackView):
    """Callback view для OIDC (поддерживает GET и POST согласно SLB ADFS)"""

    def get(self, request):
        """
        GET метод - основной для SLB ADFS (code приходит в query параметрах)
        Согласно документации: https://auth.slb.ru/adfs/oauth2/authorize возвращает
        редирект на callback URL с параметрами: ?code=xxx&state=xxx
        """
        try:
            logger.info("OIDC GET callback received")

            # Получаем параметры из query string
            code = request.GET.get('code')
            state = request.GET.get('state')
            error = request.GET.get('error')
            error_description = request.GET.get('error_description')

            logger.debug(f"GET params - code: {bool(code)}, state: {state}, error: {error}")

            # Проверяем ошибки
            if error:
                logger.error(f"ADFS error: {error} - {error_description}")
                return self.handle_error(error, error_description)

            if not code:
                logger.error("Missing authorization code in GET request")
                return self.handle_error('missing_code', 'Missing authorization code or state')

            # Валидируем state (защита от CSRF)
            if not self.validate_state(state, request):
                logger.error(f"Invalid state parameter: {state}")
                return self.handle_error('invalid_state', 'State validation failed')

            # Обмениваем code на токены
            tokens = self.exchange_code_for_tokens(code, request)
            if not tokens:
                logger.error("Failed to exchange code for tokens")
                return self.handle_error('token_exchange_failed', 'Failed to get tokens')

            # Валидируем и декодируем токены
            user_info = self.validate_and_process_tokens(tokens, request)
            if not user_info:
                logger.error("Failed to validate tokens")
                return self.handle_error('token_validation_failed', 'Token validation failed')

            # Аутентифицируем пользователя
            user = self.authenticate_user(user_info, request)
            if not user:
                logger.error("Failed to authenticate user - not found in database")
                return JsonResponse({
                    'success': False,
                    'error': 'user_not_found',
                    'error_description': 'Your account is not registered in the system. Please contact your administrator.',
                    'debug': {
                        'tried_alias': getattr(self, '_failed_alias', '?'),
                        'email_from_adfs': getattr(self, '_failed_email', '?'),
                        'upn_from_adfs': getattr(self, '_failed_upn', '?'),
                        'unique_name_from_adfs': getattr(self, '_failed_unique_name', '?'),
                        'claims_keys': getattr(self, '_failed_claims_keys', []),
                    }
                }, status=401)

            # Логиним пользователя
            self.login_user(user, request)

            logger.info(f"User {user.alias} successfully authenticated via GET callback")

            # Возвращаем успешный ответ
            return self.handle_success(user, request)

        except Exception as e:
            logger.exception(f"Unhandled exception in GET callback: {e}")
            return self.handle_error('internal_error', str(e))

    def post(self, request):
        """
        Основной метод для обработки OIDC callback через POST
        OIDC провайдер отправляет: code, state, session_state в теле запроса
        """
        try:
            logger.info("OIDC POST callback received")

            # Получаем параметры из POST тела
            code = request.POST.get('code')
            state = request.POST.get('state')
            session_state = request.POST.get('session_state')
            error = request.POST.get('error')

            logger.debug(f"POST params - code: {bool(code)}, state: {state}, error: {error}")

            # Проверяем ошибки
            if error:
                error_description = request.POST.get('error_description', '')
                logger.error(f"OIDC error: {error} - {error_description}")
                return self.handle_error(error, error_description)

            if not code:
                logger.error("No authorization code in POST request")
                return self.handle_error('missing_code', 'Authorization code is missing')

            # Валидируем state (защита от CSRF)
            if not self.validate_state(state, request):
                logger.error(f"Invalid state parameter: {state}")
                return self.handle_error('invalid_state', 'State validation failed')

            # Обмениваем code на токены
            tokens = self.exchange_code_for_tokens(code, request)
            if not tokens:
                logger.error("Failed to exchange code for tokens")
                return self.handle_error('token_exchange_failed', 'Failed to get tokens')

            # Валидируем и декодируем ID токен
            user_info = self.validate_and_process_tokens(tokens, request)
            if not user_info:
                logger.error("Failed to validate tokens")
                return self.handle_error('token_validation_failed', 'Token validation failed')

            # Аутентифицируем пользователя
            user = self.authenticate_user(user_info, request)
            if not user:
                logger.error("Failed to authenticate user - not found in database")
                return JsonResponse({
                    'success': False,
                    'error': 'user_not_found',
                    'error_description': 'Your account is not registered in the system. Please contact your administrator.',
                    'debug': {
                        'tried_alias': getattr(self, '_failed_alias', '?'),
                        'email_from_adfs': getattr(self, '_failed_email', '?'),
                        'upn_from_adfs': getattr(self, '_failed_upn', '?'),
                        'unique_name_from_adfs': getattr(self, '_failed_unique_name', '?'),
                        'claims_keys': getattr(self, '_failed_claims_keys', []),
                    }
                }, status=401)

            # Логиним пользователя
            self.login_user(user, request)

            logger.info(f"User {user.alias} successfully authenticated via POST callback")

            # Возвращаем успешный ответ
            return self.handle_success(user, request)

        except Exception as e:
            logger.exception(f"Unhandled exception in POST callback: {e}")
            return self.handle_error('internal_error', str(e))

    def validate_state(self, state, request):
        """Валидация state параметра (защита от CSRF)"""
        # Получаем state из сессии
        session_state = request.session.get('oidc_state')

        if not session_state:
            logger.warning("No state in session")
            return False

        if state != session_state:
            logger.warning(f"State mismatch: session={session_state}, received={state}")
            return False

        # Очищаем использованный state
        if 'oidc_state' in request.session:
            del request.session['oidc_state']

        return True

    def exchange_code_for_tokens(self, code, request):
        """Обмен authorization code на access и ID токены"""
        import requests
        from urllib.parse import urlencode

        # Получаем redirect_uri
        redirect_uri = request.session.get('oidc_redirect_uri')
        if not redirect_uri and hasattr(settings, 'OIDC_REDIRECT_URI'):
            redirect_uri = settings.OIDC_REDIRECT_URI

        logger.debug(f"Exchanging code, redirect_uri: {redirect_uri}")

        # Подготавливаем запрос
        token_data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': redirect_uri,
            'client_id': settings.OIDC_RP_CLIENT_ID,
            'client_secret': settings.OIDC_RP_CLIENT_SECRET,
        }

        # Дополнительные параметры если нужны
        token_data.update(import_from_settings('OIDC_AUTH_REQUEST_EXTRA_PARAMS', {}))

        try:
            # Отправляем запрос к провайдеру
            response = requests.post(
                settings.OIDC_OP_TOKEN_ENDPOINT,
                data=token_data,
                headers={
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Accept': 'application/json'
                },
                timeout=30
            )

            if response.status_code == 200:
                tokens = response.json()
                logger.debug(f"Token exchange successful, token_type: {tokens.get('token_type')}")

                # Сохраняем токены в сессии
                request.session['oidc_access_token'] = tokens.get('access_token')
                request.session['oidc_id_token'] = tokens.get('id_token')
                request.session['oidc_refresh_token'] = tokens.get('refresh_token')

                return tokens
            else:
                logger.error(f"Token exchange failed: {response.status_code} - {response.text}")
                return None

        except requests.RequestException as e:
            logger.error(f"Request failed during token exchange: {e}")
            return None

    def validate_and_process_tokens(self, tokens, request):
        """Валидация токенов и получение userinfo (согласно SLB ADFS)"""
        id_token = tokens.get('id_token')
        access_token = tokens.get('access_token')
        
        if not id_token and not access_token:
            logger.error("No tokens in response")
            return None

        try:
            # Для ADFS с scope=allatclaims данные приходят в access_token
            # Декодируем токен без валидации (для разработки)
            # В продакшене следует валидировать через JWKS
            import jwt
            
            if id_token:
                # Декодируем ID токен
                claims = jwt.decode(
                    id_token, 
                    options={"verify_signature": False}  # ВНИМАНИЕ: в продакшене включите валидацию!
                )
                logger.info(f"ID Token claims keys: {list(claims.keys())}")
                logger.info(f"ID Token claims: email={claims.get('email')}, upn={claims.get('upn')}, unique_name={claims.get('unique_name')}, sub={claims.get('sub')}")
            else:
                claims = {}

            # Получаем userinfo из access token или через API
            user_info = self.get_userinfo(access_token, claims)

            return user_info

        except Exception as e:
            logger.error(f"Token processing failed: {e}")
            logger.exception(e)
            return None

    def get_userinfo(self, access_token, claims):
        """Получение userinfo от провайдера"""
        import requests

        # Если claims уже содержат всю информацию, можно пропустить
        if claims.get('email') and claims.get('sub'):
            logger.info("Using claims from ID token (has email+sub)")
            return claims

        # Пробуем декодировать access_token — ADFS часто кладёт claims туда
        if access_token:
            try:
                access_claims = jwt.decode(
                    access_token,
                    options={"verify_signature": False}
                )
                logger.info(f"Access token claims keys: {list(access_claims.keys())}")
                logger.info(f"Access token: email={access_claims.get('email')}, upn={access_claims.get('upn')}, unique_name={access_claims.get('unique_name')}")
                # Мёржим: данные access_token поверх ID token claims
                merged = {**claims, **access_claims}
                if merged.get('email') or merged.get('upn') or merged.get('unique_name'):
                    logger.info("Using merged claims from access_token")
                    return merged
            except Exception as e:
                logger.warning(f"Could not decode access_token: {e}")

        # Запрашиваем userinfo endpoint
        if not access_token or not settings.OIDC_OP_USER_ENDPOINT:
            logger.warning(f"No access token or userinfo endpoint configured, claims only has: {list(claims.keys())}")
            return claims

        try:
            logger.info(f"Calling userinfo endpoint: {settings.OIDC_OP_USER_ENDPOINT}")
            response = requests.get(
                settings.OIDC_OP_USER_ENDPOINT,
                headers={'Authorization': f'Bearer {access_token}'},
                timeout=10,
                verify=False  # ADFS может использовать внутренний сертификат
            )

            logger.info(f"Userinfo response status: {response.status_code}")
            if response.status_code == 200:
                user_info = response.json()
                logger.info(f"Userinfo received keys: {list(user_info.keys())}")
                logger.info(f"Userinfo: email={user_info.get('email')}, upn={user_info.get('upn')}, unique_name={user_info.get('unique_name')}")
                return user_info
            else:
                logger.warning(f"Userinfo request failed: {response.status_code}, body: {response.text[:200]}")
                return claims

        except Exception as e:
            logger.warning(f"Failed to get userinfo: {e}")
            return claims

    def authenticate_user(self, user_info, request):
        """Аутентификация/создание пользователя"""
        from users.backends import OIDCAuthenticationBackend

        # Используем кастомный бэкенд для SLB ADFS
        backend = OIDCAuthenticationBackend()
        backend.request = request

        # Ищем существующего пользователя по claims (unique_name/email)
        users = backend.filter_users_by_claims(user_info)

        if users.exists():
            user = users.first()
            logger.info(f"Found existing user: {user.alias}")
            # Обновляем email если изменился (другие поля — только через админку)
            email = user_info.get('email')
            if email and user.email != email:
                user.email = email
                user.save(update_fields=['email'])
            return user

        # Пользователя нет в БД — возвращаем диагностику прямо в ответе
        email = user_info.get('email', '')
        upn = user_info.get('upn', '')
        unique_name = user_info.get('unique_name', '')

        # Определяем какой alias был использован для поиска
        if email and '@' in email:
            tried_alias = email.split('@')[0]
        elif upn and '@' in upn:
            tried_alias = upn.split('@')[0]
        elif unique_name:
            tried_alias = unique_name.split('\\')[-1] if '\\' in unique_name else unique_name
        else:
            tried_alias = '(no claims)'

        logger.error(
            f"OIDC login failed: tried alias='{tried_alias}', "
            f"email='{email}', upn='{upn}', unique_name='{unique_name}', "
            f"all claims keys: {list(user_info.keys())}"
        )
        # Сохраняем в request для диагностического ответа
        self._failed_alias = tried_alias
        self._failed_claims_keys = list(user_info.keys())
        self._failed_email = email
        self._failed_upn = upn
        self._failed_unique_name = unique_name
        return None

    def login_user(self, user, request):
        """Логин пользователя в Django сессию"""
        # Модель Users не наследует AbstractUser, поэтому используем сессию напрямую
        # вместо django.contrib.auth.login()
        request.session['_auth_user_id'] = str(user.pk)
        request.session['_auth_user_backend'] = 'users.backends.OIDCAuthenticationBackend'
        request.session['_auth_user_hash'] = ''
        request.session['oidc_login'] = True
        request.session['oidc_user_alias'] = user.alias
        request.session.save()
        logger.info(f"Session created for user {user.alias} (pk={user.pk})")

    def handle_success(self, user, request):
        """Обработка успешной аутентификации
        
        Session cookie уже установлен через login_user().
        Редиректим на главную страницу SPA без токенов в URL (безопасно).
        """
        # Определяем куда редиректить (по умолчанию - главная страница SPA)
        next_url = request.POST.get('next') or request.GET.get('next')
        
        # Проверяем безопасность URL
        if not next_url or not self.is_safe_url(next_url):
            next_url = '/'  # Главная страница SPA
        
        # Редиректим на фронтенд
        # Session cookie автоматически установлен через SessionMiddleware
        logger.info(f"Redirecting authenticated user {user.alias} to {next_url}")
        return HttpResponseRedirect(next_url)

    def handle_error(self, error_code, error_description):
        """Обработка ошибок"""
        # Можно сохранить ошибку в сессии для отображения
        # request.session['oidc_error'] = error_code
        # request.session['oidc_error_description'] = error_description

        # Возвращаем JSON с ошибкой
        return JsonResponse({
            'success': False,
            'error': error_code,
            'error_description': error_description
        }, status=400)

    def get_success_redirect_url(self, request):
        """Получение URL для редиректа после успешного входа"""
        # 1. Из параметра next
        next_url = request.POST.get('next') or request.GET.get('next')
        if next_url and self.is_safe_url(next_url):
            return next_url

        # 2. Из сессии
        next_url = request.session.pop('next', None)
        if next_url and self.is_safe_url(next_url):
            return next_url

        # 3. Из настроек
        if hasattr(settings, 'LOGIN_REDIRECT_URL'):
            return settings.LOGIN_REDIRECT_URL

        # 4. По умолчанию
        return '/'

    def is_safe_url(self, url):
        """Проверка безопасности URL"""
        from django.utils.http import url_has_allowed_host_and_scheme
        allowed_hosts = set(settings.ALLOWED_HOSTS)
        allowed_hosts.add(self.request.get_host())
        return url_has_allowed_host_and_scheme(url, allowed_hosts=allowed_hosts)

class UserInfoAPIView(APIView):
    """Получение информации о текущем пользователе и OIDC claims"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # Способ 1: Получение claims из ID токена (если он хранится в сессии)
        oidc_data = self._get_oidc_data_from_session(request)

        # Способ 2: Получение информации о пользователе через бэкенд
        backend_data = self._get_user_info_from_backend(request.user)

        return Response({
            'django_user': {
                'id': user.id,
                'alias': user.alias,
                'email': user.email,
                'first_name': user.first_name,
                'second_name': user.second_name,
                'is_active': user.is_active,
            },
            'oidc_session_data': oidc_data,
            'backend_info': backend_data,
            'is_authenticated': user.is_authenticated,
            'session_keys': list(request.session.keys()),
        })

    def _get_oidc_data_from_session(self, request):
        """Извлечение OIDC данных из сессии"""
        session_data = {}

        # Проверяем наличие OIDC данных в сессии
        if hasattr(request.session, 'session_key'):
            # ID токен
            id_token = request.session.get('oidc_id_token')
            if id_token:
                try:
                    # Декодируем ID токен без верификации (только для отображения)
                    # Внимание: не используйте это для безопасности!
                    decoded = jwt.decode(id_token, options={"verify_signature": False})
                    session_data['id_token_decoded'] = decoded
                except (jwt.DecodeError, jwt.InvalidTokenError) as e:
                    session_data['id_token_error'] = str(e)

                session_data['id_token_present'] = True

            # Access токен
            access_token = request.session.get('oidc_access_token')
            if access_token:
                session_data['access_token_present'] = True
                # Можно показать часть токена (первые и последние символы)
                if len(access_token) > 20:
                    session_data['access_token_sample'] = f"{access_token[:10]}...{access_token[-10:]}"

            # Refresh токен
            refresh_token = request.session.get('oidc_refresh_token')
            if refresh_token:
                session_data['refresh_token_present'] = True

            # Другие OIDC данные из сессии
            oidc_keys = [k for k in request.session.keys() if k.startswith('oidc_')]
            for key in oidc_keys:
                if key not in ['oidc_id_token', 'oidc_access_token', 'oidc_refresh_token']:
                    session_data[key] = request.session.get(key)

        return session_data

    def _get_user_info_from_backend(self, user):
        """Получение информации через бэкенд аутентификации"""
        from django.contrib.auth import authenticate
        from mozilla_django_oidc.auth import OIDCAuthenticationBackend

        backend_info: dict[str, Any] = {
            'auth_backends': []
        }

        # Проверяем, какой бэкенд использовался
        for backend_path in user._meta.backends:
            backend_info['auth_backends'].append(str(backend_path))

            # Если это OIDC бэкенд, можем получить дополнительную информацию
            if 'oidc' in backend_path.lower():
                backend_info['is_oidc_backend'] = True

        return backend_info


class OIDCLoginAPIView(APIView):
    """OIDC login как API endpoint"""
    permission_classes = [AllowAny]  # ← ВАЖНО: разрешаем доступ всем

    def get(self, request):
        # Получаем redirect_uri
        redirect_uri = getattr(settings, 'OIDC_REDIRECT_URI', None)

        if not redirect_uri:
            from django.urls import reverse
            redirect_uri = request.build_absolute_uri(
                reverse('oidc_authentication_callback')
            )

        # Генерируем state и nonce
        state = secrets.token_urlsafe(16)
        nonce = secrets.token_urlsafe(16)

        # Сохраняем в сессии
        request.session['oidc_state'] = state
        request.session['oidc_nonce'] = nonce
        request.session['oidc_redirect_uri'] = redirect_uri

        # Формируем OIDC запрос (согласно SLB ADFS документации)
        params = {
            'client_id': settings.OIDC_RP_CLIENT_ID,
            'response_type': 'code',
            'scope': settings.OIDC_RP_SCOPES,  # openid profile email
            'redirect_uri': redirect_uri,
            'state': state,
            # nonce не используется для базового flow
            # response_mode по умолчанию - query (GET запрос)
        }

        # Формируем URL
        auth_url = settings.OIDC_OP_AUTHORIZATION_ENDPOINT
        redirect_url = f"{auth_url}?{urlencode(params)}"

        # Логируем для отладки
        logger.info(f"OIDC Authentication Request:")
        logger.info(f"  CLIENT_ID: {settings.OIDC_RP_CLIENT_ID}")
        logger.info(f"  REDIRECT_URI: {redirect_uri}")
        logger.info(f"  SCOPE: {settings.OIDC_RP_SCOPES}")
        logger.info(f"  AUTH_URL: {redirect_url}")

        # Возвращаем JSON с URL для клиентского редиректа (для AJAX запросов)
        # Фронтенд должен сделать: window.location.href = data.auth_url
        return Response({
            'auth_url': redirect_url,
            'message': 'Redirect to OIDC provider'
        }, status=status.HTTP_200_OK)

class ProtectedAPIView(APIView):
    """Пример защищенного API endpoint с OIDC"""
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Получение защищенных данных",
        responses={
            200: openapi.Response(
                description="Success",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'user': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'username': openapi.Schema(type=openapi.TYPE_STRING),
                                'email': openapi.Schema(type=openapi.TYPE_STRING),
                            }
                        ),
                        'oidc_info': openapi.Schema(type=openapi.TYPE_OBJECT),
                    }
                )
            ),
            401: "Unauthorized"
        },
        security=[{'OIDC': ['openid', 'email', 'profile']}]
    )
    def get(self, request):
        user = request.user

        # Получаем OIDC информацию
        oidc_info = self._extract_oidc_info(request)

        return Response({
            'message': 'Доступ разрешен через OIDC',
            'user': {
                'id': user.id,
                'alias': user.alias,
                'email': user.email,
                'first_name': user.first_name,
                'second_name': user.second_name,
            },
            'oidc_info': oidc_info,
            'auth_method': 'OIDC' if request.session.get('oidc_id_token') else 'Django',
            'session_age': request.session.get_expiry_age(),
        })

    def _extract_oidc_info(self, request):
        """Извлечение OIDC информации из запроса"""
        info = {
            'has_oidc_session': False,
            'tokens': {},
            'claims': {}
        }

        # Проверяем OIDC токены в сессии
        id_token = request.session.get('oidc_id_token')
        if id_token:
            info['has_oidc_session'] = True
            info['tokens']['id_token_present'] = True

            try:
                # Декодируем ID токен для получения claims
                decoded = jwt.decode(id_token, options={"verify_signature": False})
                info['claims'] = {
                    'sub': decoded.get('sub'),
                    'email': decoded.get('email'),
                    'email_verified': decoded.get('email_verified'),
                    'name': decoded.get('name'),
                    'preferred_username': decoded.get('preferred_username'),
                    'given_name': decoded.get('given_name'),
                    'family_name': decoded.get('family_name'),
                    'iss': decoded.get('iss'),
                    'aud': decoded.get('aud'),
                    'exp': decoded.get('exp'),
                    'iat': decoded.get('iat'),
                    'auth_time': decoded.get('auth_time'),
                }
            except Exception as e:
                info['claims']['error'] = str(e)

        access_token = request.session.get('oidc_access_token')
        if access_token:
            info['tokens']['access_token_present'] = True

        refresh_token = request.session.get('oidc_refresh_token')
        if refresh_token:
            info['tokens']['refresh_token_present'] = True

        return info


class OIDCConfigView(APIView):
    """Получение конфигурации OIDC"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from django.conf import settings

        config = {
            'client_id': getattr(settings, 'OIDC_RP_CLIENT_ID', None),
            'authorization_endpoint': getattr(settings, 'OIDC_OP_AUTHORIZATION_ENDPOINT', None),
            'token_endpoint': getattr(settings, 'OIDC_OP_TOKEN_ENDPOINT', None),
            'userinfo_endpoint': getattr(settings, 'OIDC_OP_USER_ENDPOINT', None),
            'jwks_endpoint': getattr(settings, 'OIDC_OP_JWKS_ENDPOINT', None),
            'scopes': getattr(settings, 'OIDC_RP_SCOPES', 'openid email profile'),
            'signing_algorithm': getattr(settings, 'OIDC_RP_SIGN_ALGO', 'RS256'),
            'store_tokens': getattr(settings, 'OIDC_STORE_ACCESS_TOKEN', False),
            'store_id_token': getattr(settings, 'OIDC_STORE_ID_TOKEN', False),
        }

        return Response(config)


# Декоратор для проверки OIDC аутентификации
def oidc_login_required(view_func=None, redirect_field_name='next'):
    """
    Декоратор, который проверяет, что пользователь аутентифицирован через OIDC
    """

    def decorator(view_func):
        @login_required(redirect_field_name=redirect_field_name)
        def _wrapped_view(request, *args, **kwargs):
            # Проверяем, есть ли OIDC токен в сессии
            if not request.session.get('oidc_id_token'):
                # Если нет OIDC токена, но пользователь аутентифицирован через Django,
                # можно редиректить на OIDC login или возвращать ошибку
                from django.http import HttpResponseForbidden
                return HttpResponseForbidden("OIDC authentication required")

            return view_func(request, *args, **kwargs)

        return _wrapped_view

    if view_func:
        return decorator(view_func)
    return decorator


# View с проверкой OIDC
@method_decorator(oidc_login_required, name='dispatch')
class StrictOIDCView(APIView):
    """View, требующий строго OIDC аутентификации"""

    def get(self, request):
        return Response({
            'message': 'Этот endpoint доступен только через OIDC аутентификацию',
            'oidc_token_present': True,
            'user': request.user.alias,
        })


class OIDCClaimsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from tsdp_backend.oidc_utils import get_oidc_claims, get_oidc_user_info, is_oidc_authenticated

        claims = get_oidc_claims(request)
        user_info = get_oidc_user_info(request)

        return Response({
            'claims': claims,
            'user_info': user_info,
            'is_oidc': is_oidc_authenticated(request),
        })


class OIDCConfigDiagnosticView(APIView):
    """Диагностика OIDC конфигурации (только для DEBUG режима)"""
    permission_classes = [AllowAny]

    def get(self, request):
        redirect_uri = getattr(settings, 'OIDC_REDIRECT_URI', None)
        if not redirect_uri:
            from django.urls import reverse
            redirect_uri = request.build_absolute_uri(
                reverse('oidc_authentication_callback')
            )
        
        # Формируем auth URL как в реальном запросе
        state = 'diagnostic-test'
        params = {
            'client_id': settings.OIDC_RP_CLIENT_ID,
            'response_type': 'code',
            'scope': settings.OIDC_RP_SCOPES,
            'redirect_uri': redirect_uri,
            'state': state,
        }
        auth_url = settings.OIDC_OP_AUTHORIZATION_ENDPOINT
        test_redirect_url = f"{auth_url}?{urlencode(params)}"
        
        return Response({
            'oidc_config': {
                'client_id': settings.OIDC_RP_CLIENT_ID,
                'client_secret_set': bool(settings.OIDC_RP_CLIENT_SECRET),
                'redirect_uri': redirect_uri,
                'scope': settings.OIDC_RP_SCOPES,
                'authorization_endpoint': settings.OIDC_OP_AUTHORIZATION_ENDPOINT,
                'token_endpoint': settings.OIDC_OP_TOKEN_ENDPOINT,
                'userinfo_endpoint': settings.OIDC_OP_USER_ENDPOINT,
                'jwks_endpoint': settings.OIDC_OP_JWKS_ENDPOINT,
                'use_nonce': settings.OIDC_USE_NONCE,
            },
            'test_auth_url': test_redirect_url,
            'instructions': {
                'message': 'Диагностика OIDC конфигурации',
                'common_issues': [
                    'CLIENT_ID не совпадает с зарегистрированным в ADFS',
                    'redirect_uri не совпадает (проверьте точное совпадение, включая trailing slash)',
                    'Scope "allatclaims" не разрешен для вашего приложения',
                    'Приложение не активировано в ADFS'
                ]
            }
        })


class AuthMeView(APIView):
    """
    GET /api/portal/auth/me/
    Возвращает текущего залогиненного пользователя (по session cookie).
    Если не залогинен — 401.
    Фронтенд использует этот endpoint чтобы проверить статус аутентификации.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        # Проверяем сессию вручную (модель Users не AbstractUser)
        user_id = request.session.get('_auth_user_id')
        if not user_id:
            return Response({'authenticated': False}, status=401)

        try:
            from .models import Users
            user = Users.objects.get(pk=user_id)
            return Response({
                'authenticated': True,
                'user': {
                    'id': user.id,
                    'alias': user.alias,
                    'first_name': user.first_name,
                    'second_name': user.second_name,
                    'email': user.email,
                    'job_title': user.job_title,
                    'is_manager': user.is_manager,
                }
            })
        except Exception as e:
            logger.warning(f"AuthMeView: user_id={user_id} not found: {e}")
            return Response({'authenticated': False}, status=401)