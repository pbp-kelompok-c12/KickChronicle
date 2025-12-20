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
    path('favorites/', views.favorite_list, name='favorite_list'),

    path('mobile/highlight/<uuid:highlight_id>/comment/', views.add_comment_mobile, name='mobile_add_comment'),
      path(
        'mobile/highlight/<uuid:highlight_id>/comments/',
        views.get_comments_mobile,
        name='mobile_get_comments'
    ),
    path('mobile/highlight/<uuid:highlight_id>/favorite/', views.toggle_favorite_mobile, name='mobile_toggle_favorite'),
    path('mobile/submit-rating/', views.submit_rating_mobile, name='mobile_submit_rating'),
    path('mobile/comments/<int:comment_id>/delete/', views.delete_comment_mobile, name='mobile_delete_comment'),
    path('mobile/favorites/', views.favorite_list_mobile, name='mobile_favorite_list'),
    path('mobile/top-rated/', views.top_rated_mobile, name='mobile_top_rated'),
    path(
    'mobile/rating/<uuid:highlight_id>/',
    views.get_user_rating_mobile,
    name='mobile_get_user_rating'
    ),
]
