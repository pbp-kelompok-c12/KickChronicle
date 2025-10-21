from django.urls import path
from . import views

app_name = 'kalender'

urlpatterns = [
    path('export/<int:kalender_id>/', views.export_kalender_ics, name='export_kalender'),
]