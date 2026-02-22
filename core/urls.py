from django.urls import path
from django.contrib.auth import views as auth_views # Import auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('log/', views.add_log, name='add_log'),
    path('edit/<int:log_id>/', views.edit_log, name='edit_log'),
    path('delete/<int:log_id>/', views.delete_log, name='delete_log'),
    path('profile/', views.profile_view, name='profile'),
    path('tips/', views.tips_view, name='tips'),
    path('ai-coach/', views.ai_analysis_view, name='ai_coach'),
    path('change-password/', views.change_password, name='change_password'),
    path('download-report/', views.download_pdf, name='download_pdf'),

    # --- PASSWORD RESET URLS ---
    path('password-reset/', 
         auth_views.PasswordResetView.as_view(template_name='core/password_reset_form.html'), 
         name='password_reset'),
    
    path('password-reset/done/', 
         auth_views.PasswordResetDoneView.as_view(template_name='core/password_reset_done.html'), 
         name='password_reset_done'),
    
    path('password-reset-confirm/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(template_name='core/password_reset_confirm.html'), 
         name='password_reset_confirm'),
    
    path('password-reset-complete/', 
         auth_views.PasswordResetCompleteView.as_view(template_name='core/password_reset_complete.html'), 
         name='password_reset_complete'),
]