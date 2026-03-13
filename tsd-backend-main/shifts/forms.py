from django import forms
from .models import Shifts, ShiftTemplates

class ShiftsForm(forms.ModelForm):
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

class ShiftTemplatesForm(forms.ModelForm):
    class Meta:
        model = ShiftTemplates
        fields = ['id',
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
                'is_office']