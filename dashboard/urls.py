from django.urls import path
from . import views

app_name = 'dashboard'


urlpatterns = [
    path('user-dashboard/', views.dashboard_view, name='dashboard'),
    # path('relapse/', views.relapse, name='log_relapse'),

    # refactored to use a single view for all relapse logging

    path('log-relapse/', views.log_relapse_confirm, name='log_relapse_confirm'),
    # # AJAX endpoint for processing the relapse confirmation
    path('dashboard/ajax/log-relapse/process/', views.log_relapse_process_ajax, name='ajax_log_relapse_process'),
    path('dashboard/ajax/log-relapse/reflect/', views.log_relapse_reflect_ajax, name='ajax_log_relapse_reflect'),
]

