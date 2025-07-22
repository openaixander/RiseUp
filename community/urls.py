from django.urls import path

from . import views

app_name = 'community'


urlpatterns = [
    path('new-post/', views.create_post_view, name='create_post'),
    path('all-post/', views.community_list_view, name='community_list'),
    path('ajax/community/toggle-like/', views.toggle_like_ajax, name='ajax_toggle_like'),
    path('community/post/<int:pk>/', views.post_detail_view, name='post_detail'),

    path('ajax/community/post/<int:pk>/comment/', views.add_comment_ajax, name='ajax_add_comment'),   
]