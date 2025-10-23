from django.forms import ModelForm
from django import forms
from highlight.models import Highlight

from django.utils.html import strip_tags

class HighlightForm(ModelForm):
    class Meta:
        model = Highlight
        fields = '__all__'

    def clean_name(self):
        name = self.cleaned_data["name"]
        return strip_tags(name)

    def clean_description(self):
        description = self.cleaned_data["description"]
        return strip_tags(description)

class HiglightFormCsv(forms.Form):
    csv_file = forms.FileField(
        label="Select CSV File (.csv)",
        help_text="Header row: Name, URL, Description, Manual Thumbnail URL (optional)",
        widget=forms.ClearableFileInput(attrs={'accept': '.csv'})
    )