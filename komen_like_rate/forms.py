# komen_like_rate/forms.py
from django import forms
from django.core.validators import MinValueValidator, MaxValueValidator
from .models import Comment

class RatingForm(forms.Form):
    value = forms.IntegerField(min_value=1, max_value=5, 
                               validators=[MinValueValidator(1), MaxValueValidator(5)])

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Enter your comment...'}),
        }