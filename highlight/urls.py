from django.urls import path
from highlight.views import show_highlight, show_main_page, add_highlight, edit_highlight, delete_highlight, add_highlights_csv
from highlight.views import highlight_json, edit_highlight_flutter, add_highlight_flutter, delete_highlight_flutter, add_highlights_csv_flutter, admin_highlight_flutter

app_name = 'highlight'

urlpatterns = [
    path('<uuid:id>/',show_highlight,name='show_highlight'),
    path('',show_main_page,name='show_main_page'),
    path('add/',add_highlight,name='add_highlight'),
    path('add/csv',add_highlights_csv,name='add_highlight_csv'),
    path('<uuid:id>/edit',edit_highlight,name='edit_highlight'),
    path('<uuid:id>/delete',delete_highlight,name='delete_highlight'),
    path('highlights-json/',highlight_json,name='highlight_json'),
    path('edit-highlight-flutter/<uuid:id>/', edit_highlight_flutter, name='edit_highlight_flutter'),
    path('add-highlight-flutter/', add_highlight_flutter, name='add_highlight_flutter'),
    path('delete-highlight-flutter/<uuid:id>/', delete_highlight_flutter, name='delete_highlight_flutter'),
    path('add-highlights-csv-flutter', add_highlights_csv_flutter, name='add_highlights_csv_flutter'),
    path('admin-highlight-flutter/', admin_highlight_flutter, name='admin_highlight_flutter'),
]