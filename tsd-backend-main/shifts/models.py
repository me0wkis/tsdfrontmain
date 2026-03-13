from datetime import datetime

from django.db import models
from django.utils import timezone

import users.models


class ShiftPatterns(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    rules = models.JSONField(default='{}')
    class Meta:
        # This model is not managed by Django migrations
        managed = False
        db_table = 'tsd_shift_patterns'

class ShiftTypes(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)
    code = models.CharField(max_length=1)
    is_work_shift = models.BooleanField()

    class Meta:
        # This model is not managed by Django migrations
        managed = False
        db_table = 'tsd_shift_types'

class ShiftTemplates(models.Model):
    id = models.AutoField(primary_key=True)
    code = models.CharField(max_length=20,blank=True)
    description = models.CharField(max_length=100)
    is_fixed_time = models.BooleanField(default=False)
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    lunch_start_time = models.TimeField(null=True, blank=True)
    lunch_end_time = models.TimeField(null=True, blank=True)
    shift_type = models.ForeignKey(ShiftTypes, on_delete=models.CASCADE)
    icon = models.CharField(max_length=50, blank=True)
    allowed_roles = models.CharField(max_length=100,blank=True)
    is_active = models.BooleanField()
    is_office = models.BooleanField()
    color = models.CharField(max_length=7)

    class Meta:
        # This model is not managed by Django migrations
        managed = False
        db_table = 'tsd_shift_templates'

class Shifts(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey('users.Users', on_delete=models.CASCADE, related_name='shifts_as_user')
    shift_date = models.DateField()
    job_title = models.CharField(max_length=50)
    shift_type = models.ForeignKey(ShiftTypes, on_delete=models.CASCADE)
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    lunch_start_time = models.TimeField(null=True, blank=True)
    lunch_end_time = models.TimeField(null=True, blank=True)
    work_hours = models.DecimalField(max_digits=4, decimal_places=2)
    shift_template = models.ForeignKey(ShiftTemplates, on_delete=models.CASCADE)
    created_by = models.ForeignKey('users.Users', on_delete=models.CASCADE, related_name='shifts_as_creator',db_column='created_by')

    class Meta:
        # This model is not managed by Django migrations
        managed = False
        db_table = 'tsd_shifts'

    def save(self, *args, **kwargs):
        total_time = datetime.combine(self.shift_date, self.end_time) - datetime.combine(self.shift_date,
                                                                                         self.start_time)

        lunch_time = datetime.combine(self.shift_date, self.lunch_end_time) - datetime.combine(self.shift_date,
                                                                                               self.lunch_start_time)
        work_time = total_time - lunch_time
        self.work_hours = round(work_time.total_seconds() / 3600, 2)
        super().save(*args, **kwargs)

class Schedule(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey('users.Users', on_delete=models.CASCADE)
    shift = models.ForeignKey(Shifts, on_delete=models.CASCADE)

class CalendarAnomalyTypes(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=30)

    class Meta:
        managed = False
        db_table = 'tsd_calendar_anomaly_types'

class CalendarAnomalies(models.Model):
    id = models.AutoField(primary_key=True)
    date = models.DateField()
    name = models.CharField(max_length=50)
    type= models.ForeignKey(CalendarAnomalyTypes, on_delete=models.CASCADE)

    class Meta:
        managed = False
        db_table = 'tsd_calendar_anomalies'

class ShiftExchange(models.Model):
    """Модель запроса на обмен сменами"""
    id = models.AutoField(primary_key=True)
    shift_from = models.ForeignKey(
        Shifts,
        on_delete=models.CASCADE,
        related_name='shift_from_id'
    )
    shift_to = models.ForeignKey(
        Shifts,
        on_delete=models.CASCADE,
        related_name='shift_to_id'
    )
    is_approved = models.BooleanField(default=False)
    created_by = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    approved_by = models.CharField(max_length=255, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        managed = False
        db_table = 'tsd_shift_exchanges'

    def approve_exchange(self, manager_alias):
        """Метод для подтверждения обмена и замены смен"""
        if self.is_approved:
            return False, "Обмен уже подтвержден"

        user_from = self.shift_from.user
        user_to = self.shift_to.user

        self.shift_from.user = user_to
        self.shift_to.user = user_from

        self.shift_from.save()
        self.shift_to.save()

        self.is_approved = True
        self.approved_by = manager_alias
        self.save()

        return True, "Обмен успешно подтвержден"

    def cancel_exchange(self, manager_alias):
        """Метод для отмены подтвержденного обмена и возврата смен в исходное состояние"""
        if not self.is_approved:
            return False, "Обмен еще не был подтвержден"

        current_user_from = self.shift_from.user
        current_user_to = self.shift_to.user

        self.shift_from.user = current_user_to
        self.shift_to.user = current_user_from

        self.shift_from.save()
        self.shift_to.save()

        self.is_approved = False
        self.approved_by = manager_alias
        self.save()

        return True, "Обмен успешно отменен"

    def get_exchange_history(self):
        """Получение истории изменений обмена"""
        return {
            'created': {
                'by': self.created_by,
                'at': self.created_at
            },
            'approved': {
                'by': self.approved_by
            } if self.approved_by else None,
            'last_updated': {
                'by': self.approved_by if self.approved_by else self.created_by,
                'at': self.updated_at
            }
        }