from datetime import datetime
from rest_framework import serializers

from users.serializers import UsersReadSerializer
from .models import Shifts, ShiftTemplates, ShiftTypes, CalendarAnomalyTypes, CalendarAnomalies, ShiftPatterns, \
    ShiftExchange
from users.models import Users

class ShiftTemplatesSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShiftTemplates
        fields = [
            'id',
            'code',
            'description',
            'is_fixed_time',
            'start_time',
            'end_time',
            'lunch_start_time',
            'lunch_end_time',
            'shift_type',
            'icon',
            'allowed_roles',
            'is_active',
            'is_office',
            'color',
        ]
        extra_kwargs = {
            'code': {'required': False},
            'icon': {'required': False}
        }

class ShiftTypesSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShiftTypes
        fields =[
            'id',
            'name',
            'code',
            'is_work_shift'
        ]

class ShiftsReadSerializer(serializers.ModelSerializer):
    start_time = serializers.TimeField(source='shift_template.start_time', read_only=True)
    end_time = serializers.TimeField(source='shift_template.end_time', read_only=True)
    lunch_start_time = serializers.TimeField(source='shift_template.lunch_start_time', read_only=True)
    lunch_end_time = serializers.TimeField(source='shift_template.lunch_end_time', read_only=True)
    work_hours = serializers.DecimalField(max_digits=4, decimal_places=2, read_only= True)
    user = serializers.CharField(source='user.alias')
    shift_type = serializers.CharField(source='shift_type.name')
    is_fixed_time = serializers.BooleanField(source='shift_template.is_fixed_time', read_only=True)
    shift_template = serializers.CharField(source='shift_template.description')
    created_by = serializers.CharField(source='created_by.alias')
    class Meta:
        model = Shifts
        fields = ['id',
                      'user',
                      'shift_date',
                      'job_title',
                      'shift_type',
                      'start_time',
                      'end_time',
                      'lunch_start_time',
                      'lunch_end_time',
                      'work_hours',
                      'shift_template',
                      'created_by',
                      'is_fixed_time'
                      ]

    def to_representation(self, instance):
        """Переопределяем представление данных"""
        representation = super().to_representation(instance)

        if instance.shift_template and not instance.shift_template.is_fixed_time:
            representation['start_time'] = instance.start_time
            representation['end_time'] = instance.end_time
            representation['lunch_start_time'] = instance.lunch_start_time
            representation['lunch_end_time'] = instance.lunch_end_time

        return representation

    def validate(self, data):
        """Валидация в зависимости от is_fixed_time"""
        shift_template = data.get('shift_template')

        if shift_template and shift_template.is_fixed_time:
            time_fields = ['start_time', 'end_time', 'lunch_start_time', 'lunch_end_time']
            for field in time_fields:
                if field in data and data[field] is not None:
                    raise serializers.ValidationError(
                        {field: f'Cannot set {field} manually when using fixed time template'}
                    )
        return data

    def create(self, validated_data):
        """Создание смены с автоматическим заполнением времени из шаблона"""
        shift_template = validated_data.get('shift_template')

        if shift_template and shift_template.is_fixed_time:
            validated_data['start_time'] = shift_template.start_time
            validated_data['end_time'] = shift_template.end_time
            validated_data['lunch_start_time'] = shift_template.lunch_start_time
            validated_data['lunch_end_time'] = shift_template.lunch_end_time
            validated_data['is_fixed_time'] = True

        return super().create(validated_data)

    def update(self, instance, validated_data):
        """Обновление смены с учетом фиксированного времени"""
        shift_template = validated_data.get('shift_template', instance.shift_template)

        if shift_template and shift_template.is_fixed_time:
            time_fields = ['start_time', 'end_time', 'lunch_start_time', 'lunch_end_time']
            for field in time_fields:
                if field in validated_data:
                    validated_data.pop(field)

            instance.start_time = shift_template.start_time
            instance.end_time = shift_template.end_time
            instance.lunch_start_time = shift_template.lunch_start_time
            instance.lunch_end_time = shift_template.lunch_end_time
            instance.is_fixed_time = True

        return super().update(instance, validated_data)

    def validate_shift_template(self, value):
        """Валидация шаблона смены"""
        if value.is_fixed_time and not all([
            value.start_time, value.end_time,
            value.lunch_start_time, value.lunch_end_time
        ]):
            raise serializers.ValidationError(
                "Shift template with is_fixed_time=True must have all time fields set"
            )
        return value


class ShiftsBulkCreateSerializer(serializers.ListSerializer):

    def create(self, validated_data):
        shifts = [Shifts(**item) for item in validated_data]
        return Shifts.objects.bulk_create(shifts)

    def update(self, instances, validated_data):
        instance_mapping = {instance.id: instance for instance in instances}

        data_mapping = {i: item for i, item in enumerate(validated_data)}

        updated_instances = []

        for i, instance in enumerate(instances):
            data = data_mapping.get(i, {})
            if data:
                updated_instances.append(self.child.update(instance, data))

        return updated_instances

class ShiftsWriteSerializer(serializers.ModelSerializer):
    work_hours = serializers.DecimalField(max_digits=4, decimal_places=2, read_only= True)
    class Meta:
        model = Shifts
        fields = ['id',
                      'user',
                      'shift_date',
                      'job_title',
                      'shift_type',
                      'start_time',
                      'end_time',
                      'lunch_start_time',
                      'lunch_end_time',
                      'work_hours',
                      'shift_template',
                      'created_by'
                      ]
        extra_kwargs = {
            'shift_type': {'required': False}
        }
        list_serializer_class = ShiftsBulkCreateSerializer

    def validate(self, data):
        """Валидация в зависимости от is_fixed_time"""
        shift_template = data.get('shift_template')

        if not shift_template:
            raise serializers.ValidationError(
                {"shift_template": "Shift template is required"}
            )

        data['shift_type'] = shift_template.shift_type

        if shift_template.is_fixed_time:
            data['start_time'] = shift_template.start_time
            data['end_time'] = shift_template.end_time
            data['lunch_start_time'] = shift_template.lunch_start_time
            data['lunch_end_time'] = shift_template.lunch_end_time

            time_fields = ['start_time', 'end_time', 'lunch_start_time', 'lunch_end_time']
            for field in time_fields:
                if field in data and data[field] != getattr(shift_template, field):
                    raise serializers.ValidationError(
                        {field: f'Cannot set {field} manually when using fixed time template'}
                    )
            if (shift_template.start_time and shift_template.end_time and
                    shift_template.lunch_start_time and shift_template.lunch_end_time and
                    data.get('shift_date')):
                total_time = (
                        datetime.combine(data['shift_date'], shift_template.end_time) -
                        datetime.combine(data['shift_date'], shift_template.start_time)
                )
                lunch_time = (
                        datetime.combine(data['shift_date'], shift_template.lunch_end_time) -
                        datetime.combine(data['shift_date'], shift_template.lunch_start_time)
                )
                work_time = total_time - lunch_time
                data['work_hours'] = round(work_time.total_seconds() / 3600, 2)

        return data

    def create(self, validated_data):
        """Создание смены с автоматическим заполнением времени из шаблона"""
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """Обновление смены с учетом фиксированного времени шаблона"""
        shift_template = validated_data.get('shift_template', instance.shift_template)

        if not shift_template:
            raise serializers.ValidationError(
                {"shift_template": "Shift template is required"}
            )

        validated_data['shift_type'] = shift_template.shift_type

        if shift_template.is_fixed_time:
            time_fields = ['start_time', 'end_time', 'lunch_start_time', 'lunch_end_time']
            for field in time_fields:
                if field in validated_data:
                    validated_data.pop(field)

            instance.start_time = shift_template.start_time
            instance.end_time = shift_template.end_time
            instance.lunch_start_time = shift_template.lunch_start_time
            instance.lunch_end_time = shift_template.lunch_end_time

            if (shift_template.start_time and shift_template.end_time and
                    shift_template.lunch_start_time and shift_template.lunch_end_time and
                    instance.shift_date):
                total_time = (
                        datetime.combine(instance.shift_date, shift_template.end_time) -
                        datetime.combine(instance.shift_date, shift_template.start_time)
                )
                lunch_time = (
                        datetime.combine(instance.shift_date, shift_template.lunch_end_time) -
                        datetime.combine(instance.shift_date, shift_template.lunch_start_time)
                )
                work_time = total_time - lunch_time
                instance.work_hours = round(work_time.total_seconds() / 3600, 2)

        return super().update(instance, validated_data)

class ShiftSerializer(serializers.ModelSerializer):
    short_code = serializers.SerializerMethodField()
    color = serializers.SerializerMethodField()
    class Meta:
        model = Shifts
        fields = ['id','shift_date', 'job_title', 'short_code', 'start_time', 'end_time',
                 'lunch_start_time', 'lunch_end_time', 'work_hours','color']

    def get_short_code(self,obj):
        try:
            template_code = '?'
            type_code = '?'
            if hasattr(obj, 'shift_template') and obj.shift_template:
                template_code = obj.shift_template.code
            else:
                print(f"Shift {obj.id} has no shift_template")

            if hasattr(obj, 'shift_type') and obj.shift_type:
                type_code = obj.shift_type.code
            else:
                print(f"Shift {obj.id} has no shift_type")

            return f"{template_code}{type_code}"
        except Exception as e:
            print(f"Error in shift_type_display for shift {obj.id}: {e}")
            return "??"

    def get_color(self, obj):
        try:
            if obj.shift_template and obj.shift_template.color:
                return obj.shift_template.color
            return None
        except:
            return None

class UserScheduleSerializer(serializers.ModelSerializer):
    shifts = ShiftSerializer(many=True, read_only=True)
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = Users
        fields = ['id', 'full_name', 'shifts']

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.second_name}"

class TeamScheduleSerializer(serializers.Serializer):
    team_name = serializers.CharField()
    users = UserScheduleSerializer(many=True)

class CalendarAnomalyTypesSerializer(serializers.ModelSerializer):
    class Meta:
        model = CalendarAnomalyTypes
        fields = [
            'id',
            'name'
        ]

class ShiftPatternsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShiftPatterns
        fields = [
            'id',
            'name',
            'description',
            'rules'
        ]

class CalendarAnomaliesReadSerializer(serializers.ModelSerializer):
    type = serializers.CharField(source='type.name')
    class Meta:
        model = CalendarAnomalies
        fields = [
            'id',
            'date',
            'name',
            'type'
        ]


class CalendarAnomaliesWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = CalendarAnomalies
        fields = [
            'id',
            'date',
            'name',
            'type'
        ]


class ShiftExchangeCreateSerializer(serializers.ModelSerializer):
    user_alias = serializers.CharField(write_only=True, required=True)
    class Meta:
        model = ShiftExchange
        fields = ['shift_from', 'shift_to','user_alias']

    def validate(self, data):
        """Валидация запроса на обмен"""
        shift_from = data['shift_from']
        shift_to = data['shift_to']
        user_alias = data.get('user_alias')

        try:
            user = Users.objects.get(alias=user_alias)
        except Users.DoesNotExist:
            raise serializers.ValidationError({"user_alias": "Пользователь с таким alias не найден"})

        # Проверяем, что пользователь является владельцем исходной смены
        """
        if shift_from.user != user:
            raise serializers.ValidationError(
                "Вы можете создать запрос только на обмен своей смены"
            )
        """
        if shift_from.id == shift_to.id:
            raise serializers.ValidationError(
                "Нельзя обменять смену на саму себя"
            )

        if shift_to.user == user:
            raise serializers.ValidationError(
                "Нельзя обменяться сменой с самим собой"
            )

        if ShiftExchange.objects.filter(
                shift_from=shift_from,
                shift_to=shift_to,
                is_approved=False
        ).exists():
            raise serializers.ValidationError(
                "Запрос на этот обмен уже существует"
            )
        self.context['user_alias'] = user_alias
        return data

    def create(self, validated_data):
        validated_data.pop('user_alias')
        validated_data['created_by'] = self.context.get('user_alias')
        return super().create(validated_data)


class ShiftExchangeListSerializer(serializers.ModelSerializer):
    shift_from = ShiftSerializer(read_only=True)
    shift_to = ShiftSerializer(read_only=True)
    history = serializers.SerializerMethodField()

    class Meta:
        model = ShiftExchange
        fields = [
            'id', 'shift_from', 'shift_to', 'is_approved',
            'created_by', 'created_at','approved_by', 'updated_at', 'history'
        ]

    def get_history(self, obj):
        return obj.get_exchange_history()

class ShiftExchangeApproveSerializer(serializers.ModelSerializer):
    manager_alias = serializers.CharField(write_only=True, required=True)
    class Meta:
        model = ShiftExchange
        fields = ['manager_alias']

    def validate(self, data):
        exchange = self.instance
        manager_alias = data.get('manager_alias')
        """
                try:
                    manager = Users.objects.get(alias=manager_alias)
                    if not (manager.groups.filter(name='Managers').exists() or manager.is_staff):
                        raise serializers.ValidationError(
                            {"manager_alias": "Пользователь не является менеджером"}
                        )
                except Users.DoesNotExist:
                    raise serializers.ValidationError(
                        {"manager_alias": "Менеджер с таким alias не найден"}
                    )
                """
        if exchange.is_approved:
            raise serializers.ValidationError("Этот обмен уже подтвержден")

        return data

    def update(self, instance, validated_data):
        manager_alias = validated_data.get('manager_alias')

        if instance.is_approved:
            success, message = instance.cancel_exchange(manager_alias)
        else:
            success, message = instance.approve_exchange(manager_alias)

        if not success:
            raise serializers.ValidationError(message)

        return instance


class ShiftExchangeCancelSerializer(serializers.ModelSerializer):
    manager_alias = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = ShiftExchange
        fields = ['manager_alias']

    def validate(self, data):
        exchange = self.instance

        if not exchange.is_approved:
            raise serializers.ValidationError("Этот обмен еще не был подтвержден")

        manager_alias = data.get('manager_alias')
        """
        try:
            manager = Users.objects.get(alias=manager_alias)
            if not (manager.groups.filter(name='Managers').exists() or manager.is_staff):
                raise serializers.ValidationError(
                    {"manager_alias": "Пользователь не является менеджером"}
                )
        except Users.DoesNotExist:
            raise serializers.ValidationError(
                {"manager_alias": "Менеджер с таким alias не найден"}
            )
        """
        return data

    def update(self, instance, validated_data):
        manager_alias = validated_data.get('manager_alias')
        success, message = instance.cancel_exchange(manager_alias)

        if not success:
            raise serializers.ValidationError(message)

        return instance