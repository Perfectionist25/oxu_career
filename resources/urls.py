from django.urls import path
from django.utils.translation import gettext_lazy as _
from . import views

app_name = 'resources'

urlpatterns = [
    # Public pages
    path('resources/', views.resource_list, name='list'),
    path('categories/', views.categories, name='categories'),
    path('categories/<int:pk>/', views.category_detail, name='category_detail'),
    path('career-paths/', views.career_paths, name='career_paths'),
    path('career-paths/<int:pk>/', views.career_path_detail, name='career_path_detail'),
    path('learning-tracks/<int:pk>/', views.learning_track_detail, name='learning_track_detail'),
    
    # Resource details and interactions
    path('resources/<slug:slug>/', views.resource_detail, name='resource_detail'),
    path('resources/<slug:slug>/download/', views.download_resource, name='download_resource'),
    path('resources/<slug:slug>/like/', views.like_resource, name='like_resource'),
    path('resources/<slug:slug>/review/', views.add_review, name='add_review'),
    
    # Study plans
    path('study-plans/', views.study_plans, name='study_plans'),
    path('study-plans/<int:pk>/', views.study_plan_detail, name='study_plan_detail'),
    path('study-plans/items/<int:item_id>/complete/', views.mark_item_completed, name='mark_item_completed'),
    path('study-plans/items/<int:item_id>/remove/', views.remove_from_study_plan, name='remove_from_study_plan'),
    
    # AJAX endpoints
    path('api/resource-suggestions/', views.get_resource_suggestions, name='get_resource_suggestions'),
]