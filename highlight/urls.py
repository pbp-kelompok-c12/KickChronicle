from django.urls import path
from highlight.views import show_highlight, show_main_page, add_highlight, edit_highlight

app_name = 'highlight'

urlpatterns = [
    path('<uuid:id>/',show_highlight,name='show_highlight'),
    path('',show_main_page,name='show_main_page'),
    path('add/',add_highlight,name='add_highlight'),
    path('<uuid:id>/edit',edit_highlight,name='edit_highlight'),
]