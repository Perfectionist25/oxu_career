from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # Authentication
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Profile
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('profile/', views.ProfileDetailView.as_view(), name='profile'),
    path('profile/edit/', views.ProfileUpdateView.as_view(), name='profile_edit'),
    path('profile/<int:pk>/', views.ProfileDetailView.as_view(), name='profile_detail'),
    
    # Notifications
    path('notifications/', views.notification_list, name='notifications'),
    path('notifications/<int:pk>/read/', views.mark_notification_read, name='mark_notification_read'),
    
    # Activity
    path('activity/', views.activity_log, name='activity_log'),
    
    # Skills
    path('skills/', views.skill_list, name='skill_list'),
    path('skills/add/', views.add_skill, name='add_skill'),
    path('skills/<int:pk>/remove/', views.remove_skill, name='remove_skill'),
    
    # AJAX endpoints
    path('api/notification-settings/', views.update_notification_settings, name='update_notification_settings'),
    path('api/unread-notifications/', views.get_unread_notification_count, name='unread_notification_count'),
]