from django import forms
from .models import Kalender

class ScheduleForm(forms.ModelForm):
    class Meta:
        model = Kalender
        fields = ['team_1', 'team_2', 'date', 'time']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'w-full rounded-md border-gray-300'}),
            'time': forms.TimeInput(attrs={'type': 'time', 'class': 'w-full rounded-md border-gray-300'}),
            'team_1': forms.TextInput(attrs={'class': 'w-full rounded-md border-gray-300'}),
            'team_2': forms.TextInput(attrs={'class': 'w-full rounded-md border-gray-300'}),
        }