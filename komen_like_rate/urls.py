# komen_like_rate/urls.py
from django.urls import path
from . import views

app_name = 'komen_like_rate'

urlpatterns = [
    path('highlight/<uuid:highlight_id>/comment/', views.add_comment, name='add_comment'),
    path('highlight/<uuid:highlight_id>/favorite/', views.toggle_favorite, name='toggle_favorite'),
    path('top-rated/', views.top_rated, name='top_rated'),
    path('submit-rating/', views.submit_rating, name='submit_rating'),
    path("comments/<int:comment_id>/delete/", views.delete_comment, name="delete_comment"),
    path('favorites/', views.favorite_list, name='favorite_list')

]
