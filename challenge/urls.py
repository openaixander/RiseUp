from django.urls import path

from . import views

app_name = 'challenge'


urlpatterns = [
    path('create-challenge/', views.create_challenge, name='create_challenge'),
    path('achievement/', views.achievements_view, name='achievement'),
    path('edit-challenge/<int:challenge_id>/', views.edit_challenge, name='edit_challenge'),
    path('delete-challenge/<int:challenge_id>/', views.delete_challenge, name='delete_challenge'),
]