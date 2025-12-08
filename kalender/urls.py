from django.urls import path
from . import views

app_name = 'kalender'

urlpatterns = [
    path('', views.show_calendar_page, name='schedule_index'),
    path('add/', views.add_schedule_view, name='add_schedule'),
    path('edit/<int:pk>/', views.edit_schedule_view, name='edit_schedule'),
    path('delete/<int:pk>/', views.delete_schedule_view, name='delete_schedule'),
    path('api/get_matches/', views.get_matches_api, name='get_matches_api'),
    path('export/<int:kalender_id>/', views.export_kalender_ics, name='export_kalender_ics'),
    path('detail/<int:pk>/', views.schedule_detail_view, name='schedule_detail'), 
    path('import/csv/', views.import_schedule_csv, name='import_schedule_csv'),
    path('export/csv/', views.export_schedule_csv, name='export_schedule_csv'),
    path('api/check_admin/', views.check_admin_status, name='check_admin_status'),
    path('api/import_flutter/', views.import_schedule_csv_flutter, name='import_schedule_csv_flutter'),
]