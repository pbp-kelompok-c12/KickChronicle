from django.urls import path
from . import views

app_name = 'tim'

urlpatterns = [
    path('', views.standings_page, name='standings_page'),
    path('api/standings/', views.get_standings_json, name='get_standings_json'),
    path('api/upload/', views.upload_standings_ajax, name='upload_standings_ajax'),
    path('api/seasons/', views.get_available_seasons, name='get_available_seasons'),
]
