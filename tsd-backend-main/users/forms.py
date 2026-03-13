from django import forms
from .models import Users

class UsersForm(forms.ModelForm):
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
                    'is_active'
        ]
        widgets = {
            'hiring_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean_phone_number(self):
        phone_number = self.cleaned_data['phone_number']
        if not phone_number.isdigit():
            raise forms.ValidationError("Phone number should only consist digits")
        return phone_number