from django.urls import path, reverse_lazy

# Import Django's built-in password reset views
from django.contrib.auth import views as auth_views
from . import views

from .views import CustomPasswordResetView
from .forms import CustomSetPasswordForm

app_name = 'accounts'

urlpatterns = [
    path('registration/', views.register, name='register'),
    # Uses path converters <uidb64> and <token> to capture parts of the URL
    path('activate/<str:uidb64>/<str:token>/', views.activate, name='activate'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # password reset urls

    # 1. Password Reset Request page (uses our custom view for Celery)
    path('password-reset/',
         CustomPasswordResetView.as_view(
             template_name='accounts/registration/password_reset_form.html/',
             email_template_name='accounts/registration/password_reset_email.html',
             subject_template_name='accounts/registration/password_reset_subject.txt',
             success_url=reverse_lazy('accounts:password_reset_done'),
         ), name='password_reset'),

    # 2. Password Reset Done page (confirmation email sent)
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='accounts/registration/password_reset_done.html'
    ), name='password_reset_done'),

    # 3. Password Reset Link confirmation page (where user enters new password)
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='accounts/registration/password_reset_confirm.html',
        success_url=reverse_lazy('accounts:password_reset_complete'),
        form_class=CustomSetPasswordForm,  # <<< Tell the view to use this form
    ), name='password_reset_confirm'),

    # 4. Password Reset Complete page (confirmation password changed)
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='accounts/registration/password_reset_complete.html',
    ), name='password_reset_complete'),
]


