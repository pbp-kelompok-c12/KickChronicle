from django import forms
from .models import Kalender

class ScheduleForm(forms.ModelForm):
    class Meta:
        model = Kalender
        fields = ['team_1', 'team_1_logo', 'team_2', 'team_2_logo', 'date', 'time']
        widgets = {
            'team_1': forms.TextInput(attrs={
                'class': 'w-full rounded-md border-gray-800'
            }),
            'team_1_logo': forms.URLInput(attrs={
                'class': 'w-full rounded-md border-gray-800'
            }),
            'team_2': forms.TextInput(attrs={
                'class': 'w-full rounded-md border-gray-800'
            }),
            'team_2_logo': forms.URLInput(attrs={
                'class': 'w-full rounded-md border-gray-800'
            }),
            'date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full rounded-md border-gray-800'
            }),
            'time': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'w-full rounded-md border-gray-800'
            }),
        }
