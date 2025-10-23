from django import forms

class StandingUploadForm(forms.Form):
    SEASON_CHOICES = [
        ('22/23', '2022/2023'),
        ('23/24', '2023/2024'),
        ('24/25', '2024/2025'),
    ]
    
    season = forms.ChoiceField(
        choices=SEASON_CHOICES,
        widget=forms.Select(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-600 bg-gray-700 text-white shadow-sm focus:border-primary focus:ring focus:ring-primary focus:ring-opacity-50'
        })
    )
    csv_file = forms.FileField(
        widget=forms.FileInput(attrs={
            'class': 'mt-1 block w-full text-sm text-gray-400 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-primary file:text-white hover:file:bg-primary/80',
            'accept': '.csv'
        })
    )
