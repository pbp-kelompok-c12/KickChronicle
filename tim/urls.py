from django.urls import path
from . import views

app_name = 'tim'

urlpatterns = [
    path('', views.standings_page, name='standings_page'),
    path('api/standings/', views.get_standings_json, name='get_standings_json'),
    path('api/upload/', views.upload_standings_ajax, name='upload_standings_ajax'),
    path('api/upload_flutter/', views.upload_standings_flutter, name='upload_standings_flutter'),
    path('api/seasons/', views.get_available_seasons, name='get_available_seasons'),
    path('api/check_admin/', views.check_admin_status, name='check_admin_status'),
    path('api/create/', views.create_standing_api, name='create_standing_api'),
    path('api/edit/<int:pk>/', views.edit_standing_api, name='edit_standing_api'),
    path('api/delete/<int:pk>/', views.delete_standing_api, name='delete_standing_api'),
    path('api/clear-season/', views.clear_season_api, name='clear_season_api'),
]
