from django.urls import path
from django.utils.translation import gettext_lazy as _
from . import views

app_name = 'events'

urlpatterns = [
    # Public pages
    path('', views.event_list, name='list'),
    path('calendar/', views.EventCalendarView.as_view(), name='event_calendar'),
    path('categories/', views.event_categories, name='event_categories'),
    path('<slug:slug>/', views.event_detail, name='event_detail'),
    
    # Registration
    path('<slug:slug>/register/', views.register_for_event, name='register_for_event'),
    path('<slug:slug>/cancel/', views.cancel_registration, name='cancel_registration'),
    
    # User events
    path('my-events/', views.my_events, name='my_events'),
    
    # Event management
    path('create/', views.create_event, name='create_event'),
    path('manage/', views.manage_events, name='manage_events'),
    path('<slug:slug>/registrations/', views.event_registrations, name='event_registrations'),
    
    # AJAX endpoints
    path('<slug:slug>/comment/', views.add_event_comment, name='add_event_comment'),
    path('<slug:slug>/rate/', views.submit_event_rating, name='submit_event_rating'),
]