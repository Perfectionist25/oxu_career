# urls.py
from django.urls import path
from . import views

app_name = 'events'

urlpatterns = [
    # Публичные URL
    path('', views.event_list, name='event_list'),
    path('calendar/', views.EventCalendarView.as_view(), name='event_calendar'),
    path('categories/', views.event_categories, name='categories'),
    path('event/<slug:slug>/', views.event_detail, name='event_detail'),
    
    # Пользовательские URL (требуют авторизации)
    path('create/', views.create_event, name='create_event'),
    path('edit/<slug:slug>/', views.edit_event, name='edit_event'),
    path('delete/<slug:slug>/', views.delete_event, name='delete_event'),
    path('manage_events/', views.manage_events, name='manage_events'),
    path('my-events/', views.my_events, name='my_events'),
    
    # Админ URL
    path('admin/events/', views.admin_event_list, name='admin_event_list'),
    path('admin/events/create/', views.admin_event_create, name='admin_event_create'),
    path('admin/events/<int:pk>/edit/', views.admin_event_edit, name='admin_event_edit'),
    path('admin/events/<int:pk>/delete/', views.admin_event_delete, name='admin_event_delete'),
    path('admin/events/<int:pk>/publish/', views.admin_event_publish, name='admin_event_publish'),
    path('admin/events/<int:pk>/unpublish/', views.admin_event_unpublish, name='admin_event_unpublish'),
    
    path('admin/categories/', views.admin_category_list, name='admin_category_list'),
    path('admin/categories/create/', views.admin_category_create, name='admin_category_create'),
    path('admin/categories/<int:pk>/edit/', views.admin_category_edit, name='admin_category_edit'),
    path('admin/categories/<int:pk>/delete/', views.admin_category_delete, name='admin_category_delete'),
    
    # API URL
    path('api/events/', views.api_events, name='api_events'),
    path('api/stats/', views.api_event_stats, name='api_event_stats'),
]