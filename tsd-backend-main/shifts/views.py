import json
import re
from datetime import datetime
from django.db.models import Q, Prefetch
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Shifts, ShiftTemplates, ShiftTypes, CalendarAnomalyTypes, CalendarAnomalies, ShiftPatterns, \
    ShiftExchange
from .serializers import ShiftsReadSerializer, ShiftsWriteSerializer, ShiftTemplatesSerializer, ShiftTypesSerializer, \
    TeamScheduleSerializer, CalendarAnomalyTypesSerializer, CalendarAnomaliesReadSerializer, \
    CalendarAnomaliesWriteSerializer, ShiftPatternsSerializer, ShiftExchangeCreateSerializer, \
    ShiftExchangeApproveSerializer, ShiftExchangeListSerializer, ShiftExchangeCancelSerializer
from .filters import ShiftTemplateFilter, ShiftTypeFilter
from django_filters import rest_framework as filters
from rest_framework import filters as drf_filters, generics, status, viewsets, serializers
from users.pagination import CustomLimitOffsetPagination
from users.models import Users
from users.permissions import IsManagerOrReadOnly, IsManager


class ShiftsListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsManagerOrReadOnly]
    """Создание и просмотр смен"""
    queryset = Shifts.objects.select_related('user', 'shift_type', 'shift_template', 'created_by').all()

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return ShiftsReadSerializer
        return ShiftsWriteSerializer

    def get_serializer(self, *args, **kwargs):
        if self.request.method == 'POST' and isinstance(self.request.data, list):
            kwargs['many'] = True
        return super().get_serializer(*args, **kwargs)

    pagination_class = CustomLimitOffsetPagination
    filter_backends = [filters.DjangoFilterBackend]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, many=isinstance(request.data, list))
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_bulk_create(self, serializer):
        """Массовое создание смен"""
        shifts_data = serializer.validated_data

        # Создаем все смены одним запросом
        shifts = [Shifts(**data) for data in shifts_data]
        created_shifts = Shifts.objects.bulk_create(shifts)

        # Обновляем serializer.data
        for i, shift in enumerate(created_shifts):
            serializer._data[i]['id'] = shift.id

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
            if field in ['user']:
                try:
                    user = Users.objects.get(alias=value)
                    field = 'user'
                    value = user.id
                except Users.DoesNotExist:
                    return Users.objects.none()
                except Users.MultipleObjectsReturned:
                    user = Users.objects.filter(alias=value).first()
                    field = 'user'
                    value = user.id if user else None

            elif field in ['shift_type']:
                try:
                    shift_type = ShiftTypes.objects.get(name=value)
                    field = 'shift_type'
                    value = shift_type.id
                except ShiftTypes.DoesNotExist:
                    return ShiftTypes.objects.none()
                except ShiftTypes.MultipleObjectsReturned:
                    shift_type= ShiftTypes.objects.filter(name=value).first()
                    field = 'shift_type'
                    value = shift_type.id if shift_type else None

            elif field in ['shift_template']:
                try:
                    shift_template = ShiftTemplates.objects.get(description=value)
                    field = 'shift_template'
                    value = shift_template.id
                except ShiftTemplates.DoesNotExist:
                    return ShiftTemplates.objects.none()
                except ShiftTemplates.MultipleObjectsReturned:
                    shift_template= ShiftTemplates.objects.filter(description=value).first()
                    field = 'shift_template'
                    value = shift_template.id if shift_template else None

            elif field in ['created_by']:
                try:
                    created_by = Users.objects.get(alias=value)
                    field = 'created_by'
                    value = created_by.id
                except Users.DoesNotExist:
                    return Users.objects.none()
                except Users.MultipleObjectsReturned:
                    created_by= Users.objects.filter(alias=value).first()
                    field = 'created_by'
                    value = created_by.id if created_by else None

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
        summary="Get list of shifts with advanced filtering",
        description="""
        ## Advanced Filtering System

        Use the `filter` parameter with format: **field-operator-value**

        ### Examples:
        - `filter=user-eq-IIvanov` - User equals IIvanov
        - `filter=shift_type-eq-1` - Shift type equals 1
        - `filter=shift_date-gt-2025-01-01` - Shift date after 2025-01-01

        ### Multiple Filters:
        Add multiple `filter` parameters:
        `filter=user-eq-IIvanov&filter=shift_type-eq-1`

        ### Available Operators:
        | Operator | Description | Example |
        |----------|-------------|---------|
        | `eq` | Equals | `user-eq-IIvanov` |
        | `ne` | Not equals | `shift_type-ne-1` |
        | `gt` | Greater than | `shift_date-gt-2024-01-01` |
        | `lt` | Less than | `shift_date-lt-2025-01-01` |
        | `contains` | Contains | `job_title-contains-live` |

        ### Available Fields:
        - `user`, `shift_date`, `shift_type`
        - `job_title`, `shift_template`
        - `start_time`, `created_by`
                """,
        parameters=[
            OpenApiParameter(
                name='filter',
                description='''
        Filter parameters in format: field-operator-value

        **Examples:**
        - filter=user-eq-IIvanov
        - filter=shift_type-eq-1
        - filter=shift_date-gt-2025-01-01

        **Multiple filters:** Use multiple filter parameters
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
                description='Example: ?filter=user-eq-IIvanov&filter=shift_type-eq-1',
                parameter_only=True
            ),
            OpenApiExample(
                'Sort by date and paginate',
                value={},
                description='Example: ?sort=shift_date-desc&limit=10&offset=20',
                parameter_only=True
            )
        ]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

class ShiftsRetrieveView(generics.RetrieveAPIView):
    permission_classes = [IsManagerOrReadOnly]
    """Просмотр смены"""
    queryset = Shifts.objects.select_related('user','shift_type','shift_template','created_by').all()
    serializer_class = ShiftsReadSerializer

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return ShiftsReadSerializer
        return ShiftsWriteSerializer

class ShiftsUpdateView(generics.UpdateAPIView):
    permission_classes = [IsManager]
    """Редактирование смены"""
    queryset = Shifts.objects.all()
    serializer_class = ShiftsWriteSerializer
    lookup_field = "id"

    def patch(self, request, *args, **kwargs):
        id_param = kwargs.get('id')

        if ',' in id_param:
            return self._bulk_update(request, id_param, partial=True)
        else:
            return super().patch(request, *args, **kwargs)

    def put(self, request, id, *args, **kwargs):
        id_param = kwargs.get('id')

        if ',' in id_param:
            return self._bulk_update(request, id_param, partial=False)
        else:
            return super().put(request, *args, **kwargs)

    def _bulk_update(self, request, ids_param, partial=False,**kwargs):
        try:
            ids = [int(id.strip()) for id in ids_param.split(',')]
        except ValueError:
            return Response(
                {"error": "Invalid format for IDs. Must be comma-separated integers."},
                status=status.HTTP_400_BAD_REQUEST
            )

        shifts = Shifts.objects.filter(id__in=ids).order_by('id')
        shifts_list = list(shifts)

        found_ids = [shift.id for shift in shifts_list]
        not_found_ids = list(set(ids) - set(found_ids))

        if not shifts.exists():
            return Response(
                {"error": f"No shifts found with provided IDs: {ids}"},
                status=status.HTTP_404_NOT_FOUND
            )

        update_data = []
        for shift in shifts_list:
            shift_data = request.data.copy()
            update_data.append(shift_data)

        serializer = self.get_serializer(
            shifts_list,
            data=update_data,
            many=True,
            partial=partial
        )

        if not serializer.is_valid():
            return Response(
                {"error": "Validation failed", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        updated_shifts = serializer.save()

        response_data = {
            "message": f"Successfully updated {len(updated_shifts)} shifts",
            "updated_ids": found_ids,
        }

        if not_found_ids:
            response_data["warning"] = f"Some IDs were not found: {not_found_ids}"

        return Response(response_data, status=status.HTTP_200_OK)
    def delete(self, request, id):  # Добавляем id как параметр
        # Получаем ID из URL параметра
        if not id:
            return Response(
                {"error": "ID parameter is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Проверяем, это один ID или несколько через запятую
            if ',' in str(id):
                ids = [int(id.strip()) for id in str(id).split(',')]
            else:
                ids = [int(id)]
        except ValueError:
            return Response(
                {"error": "Invalid format for IDs. Must be integers or comma-separated integers."},
                status=status.HTTP_400_BAD_REQUEST
            )

        shifts = Shifts.objects.filter(id__in=ids)
        found_ids = list(shifts.values_list('id', flat=True))
        not_found_ids = list(set(ids) - set(found_ids))

        if not shifts.exists():
            return Response(
                {"error": f"No shifts found with provided IDs: {ids}"},
                status=status.HTTP_404_NOT_FOUND
            )

        deleted_count, _ = shifts.delete()

        response_data = {
            "message": f"Successfully deleted {deleted_count} shifts",
            "deleted_ids": found_ids,
        }

        if not_found_ids:
            response_data["warning"] = f"Some IDs were not found: {not_found_ids}"

        return Response(response_data, status=status.HTTP_200_OK)

class ShiftTemplatesListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsManager]
    """Создание и просмотр шаблонов смен"""
    queryset = ShiftTemplates.objects.all()
    serializer_class = ShiftTemplatesSerializer
    pagination_class = CustomLimitOffsetPagination
    filter_backends = [
        filters.DjangoFilterBackend,
        drf_filters.SearchFilter,
        drf_filters.OrderingFilter
    ]
    filterset_class = ShiftTemplateFilter
    search_fields = ['code','name','shift_type','is_fixed_time','is_active']
    ordering_fields = ['start_time', 'end_time', 'is_fixed_time', 'shift_type', 'is_active']
    ordering = ['start_time']

class ShiftTemplatesRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsManager]
    """CRUD для шаблонов смен"""
    queryset = ShiftTemplates.objects.all()
    serializer_class = ShiftTemplatesSerializer

class ShiftTypesListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsManagerOrReadOnly]
    """Создание и просмотр типов смен"""
    queryset = ShiftTypes.objects.all()
    pagination_class = CustomLimitOffsetPagination
    serializer_class = ShiftTypesSerializer
    filter_backends = [
        filters.DjangoFilterBackend,
        drf_filters.SearchFilter,
        drf_filters.OrderingFilter
    ]
    filterset_class = ShiftTypeFilter

class ShiftTypesRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsManagerOrReadOnly]
    """CRUD для типов смен"""
    queryset = ShiftTypes.objects.all()
    serializer_class = ShiftTypesSerializer


class ScheduleView(APIView):
    permission_classes = [IsManagerOrReadOnly]
    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='include_all_active',
                type=str,
                location=OpenApiParameter.QUERY,
                description='Include all active users (1=true, 0=false)',
                enum=['0', '1'],
                default='0'
            )
        ]
    )
    def get(self, request, year, month):
        try:
            year_int = int(year)
            month_int = int(month)

            include_all_active = request.GET.get('include_all_active', '0')
            include_all_active_bool = include_all_active == '1'

            first_day = datetime(year_int, month_int, 1).date()
            if month_int == 12:
                first_day_next_month = datetime(year_int + 1, 1, 1).date()
            else:
                first_day_next_month = datetime(year_int, month_int + 1, 1).date()
            month_name = first_day.strftime('%B')

            shifts_queryset = Shifts.objects.filter(
                shift_date__gte=first_day,
                shift_date__lt=first_day_next_month
            ).select_related('shift_template', 'shift_type').order_by('shift_date')

            total_shift_count = shifts_queryset.count()

            prefetch_shifts = Prefetch(
                'shifts_as_user',
                queryset=shifts_queryset,
                to_attr='user_shifts_list'
            )

            if include_all_active_bool:
                users = Users.objects.filter(is_active=1)
            else:
                users = Users.objects.filter(
                    is_active=1,
                    shifts_as_user__shift_date__gte=first_day,
                    shifts_as_user__shift_date__lt=first_day_next_month
                ).distinct()

            users = users.select_related('team') \
                .prefetch_related(prefetch_shifts) \
                .order_by('team__team_name', 'first_name')

            users_with_enough_shifts = []
            users_with_few_shifts = []
            users_without_shifts = []

            for user in users:
                user_shifts = getattr(user, 'user_shifts_list', [])
                user.shifts = user_shifts
                shift_count = len(user_shifts)

                if shift_count == 0:
                    users_without_shifts.append(user)
                elif shift_count < 15:
                    users_with_few_shifts.append(user)
                else:
                    users_with_enough_shifts.append(user)

            users_with_enough_shifts.sort(key=lambda x: (x.team.team_name if x.team else 'ZZZ', x.first_name))
            users_with_few_shifts.sort(key=lambda x: (x.team.team_name if x.team else 'ZZZ', x.first_name))

            teams_data = {}

            for user in users_with_enough_shifts:
                team_name = user.team.team_name if user.team else 'No Team'
                if team_name not in teams_data:
                    teams_data[team_name] = {'team_name': team_name, 'users': []}
                teams_data[team_name]['users'].append(user)

            if users_with_few_shifts:
                teams_data['Few Shifts'] = {
                    'team_name': 'Few Shifts',
                    'users': users_with_few_shifts
                }

            if include_all_active_bool and users_without_shifts:
                teams_data['No Shifts'] = {
                    'team_name': 'No Shifts',
                    'users': users_without_shifts
                }

            teams_list = sorted(teams_data.values(), key=lambda x: {
                'No Shifts': 'ZZZ',
                'Few Shifts': 'ZYY',
            }.get(x['team_name'], x['team_name']))

            serializer = TeamScheduleSerializer(teams_list, many=True)

            return Response({
                'year': year_int,
                'month': month_int,
                'month_name': month_name,
                'schedule': serializer.data,
                'shift_count': total_shift_count
            })

        except Exception as e:
            import traceback
            print(f"Error: {str(e)}")
            print(traceback.format_exc())
            return Response({"error": str(e)}, status=500)

class CalendarAnomalyTypesListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsManagerOrReadOnly]
    """Создание и просмотр типов аномалий"""
    queryset = CalendarAnomalyTypes.objects.all()
    pagination_class = CustomLimitOffsetPagination
    serializer_class = CalendarAnomalyTypesSerializer

class CalendarAnomalyTypesRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsManagerOrReadOnly]
    """CRUD для типов аномалий"""
    queryset = CalendarAnomalyTypes.objects.all()
    serializer_class = CalendarAnomalyTypesSerializer

class CalendarAnomaliesListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsManager]
    """Создание и просмотр аномалий"""
    queryset = CalendarAnomalies.objects.all()
    pagination_class = CustomLimitOffsetPagination
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return CalendarAnomaliesReadSerializer
        return CalendarAnomaliesWriteSerializer

class CalendarAnomaliesRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsManager]
    """CRUD для аномалий"""
    queryset = CalendarAnomalies.objects.all()

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return CalendarAnomaliesReadSerializer
        return CalendarAnomaliesWriteSerializer

@extend_schema(operation_id='calendar_anomalies_by_month')
class CalendarAnomaliesByMonthView(generics.ListAPIView):
    permission_classes = [IsManagerOrReadOnly]
    """Получение аномалий на месяц"""
    serializer_class = CalendarAnomaliesReadSerializer

    def get_queryset(self):
        year = self.kwargs['year']
        month = self.kwargs['month']

        queryset = CalendarAnomalies.objects.filter(
            Q(date__year=year) &
            Q(date__month=month)
        ).order_by('date')

        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)

        response_data = {
            'year': self.kwargs['year'],
            'month': self.kwargs['month'],
            'anomalies': serializer.data
        }

        return Response(response_data)


class CreateExchangeView(generics.CreateAPIView):
    """Создание запроса на обмен"""
    queryset = ShiftExchange.objects.all()
    permission_classes = [AllowAny]
    authentication_classes = []
    serializer_class = ShiftExchangeCreateSerializer


class ExchangeDetailView(generics.RetrieveAPIView):
    """Получение детальной информации об обмене"""
    queryset = ShiftExchange.objects.all()
    permission_classes = [AllowAny]
    authentication_classes = []
    serializer_class = ShiftExchangeListSerializer


class ApproveExchangeView(generics.UpdateAPIView):
    """Подтверждение или отмена обмена (в зависимости от текущего статуса)"""
    queryset = ShiftExchange.objects.all()
    permission_classes = [AllowAny]
    authentication_classes = []
    serializer_class = ShiftExchangeApproveSerializer

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        # Возвращаем обновленный объект
        response_serializer = ShiftExchangeListSerializer(instance)
        return Response(response_serializer.data, status=status.HTTP_200_OK)


class CancelExchangeView(generics.UpdateAPIView):
    """Отмена подтвержденного обмена"""
    queryset = ShiftExchange.objects.all()
    permission_classes = [AllowAny]
    authentication_classes = []
    serializer_class = ShiftExchangeCancelSerializer

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        response_serializer = ShiftExchangeListSerializer(instance)
        return Response(response_serializer.data, status=status.HTTP_200_OK)


class ExchangeHistoryView(generics.RetrieveAPIView):
    """Получение истории изменений обмена"""
    queryset = ShiftExchange.objects.all()
    permission_classes = [AllowAny]
    authentication_classes = []
    serializer_class = ShiftExchangeListSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        return Response({
            'exchange_id': instance.id,
            'history': instance.get_exchange_history()
        })

class ShiftPatternsListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsManager]
    """Создание и просмотр патенров смен"""
    queryset = ShiftPatterns.objects.all()
    pagination_class = CustomLimitOffsetPagination
    serializer_class = ShiftPatternsSerializer

class ShiftPatternsRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsManager]
    """CRUD для патернов смен"""
    queryset = ShiftPatterns.objects.all()
    serializer_class = ShiftPatternsSerializer