from django.urls import path
from highlight.views import show_highlight

app_name = 'highlight'

url_patterns = [
    path('',show_highlight,name='show_highlight'),
]