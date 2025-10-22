from django.urls import path
from . import views

app_name = 'kalender'

urlpatterns = [
    path("", views.show_calendar_page, name="schedule_index"),
    path("api/matches/", views.get_matches_api, name="get_matches_api"),
    path("export/<int:kalender_id>/", views.export_kalender_ics, name="export_kalender_ics"),
    path("tambah/", views.add_schedule_view, name="add_schedule"),
]
