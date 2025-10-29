# cvbuilder/urls.py
from django.urls import path
from . import views

app_name = 'cvbuilder'

urlpatterns = [
    path('', views.CVListView.as_view(), name='cv_list'),
    path('create/', views.cv_create, name='cv_create'),
    path('<int:pk>/', views.cv_detail, name='cv_detail'),
    path('<int:pk>/edit/', views.cv_edit, name='cv_edit'),
    path('<int:pk>/delete/', views.cv_delete, name='cv_delete'),
    path('<int:pk>/preview/', views.cv_preview, name='cv_preview'),
    path('<int:pk>/export-pdf/', views.cv_export_pdf, name='cv_export_pdf'),
    path('<int:pk>/duplicate/', views.cv_duplicate, name='cv_duplicate'),
    path('<int:pk>/update-status/', views.update_cv_status, name='update_cv_status'),
    
    # AJAX endpoints
    path('<int:pk>/add-education/', views.add_education, name='add_education'),
    path('<int:pk>/add-experience/', views.add_experience, name='add_experience'),
    path('<int:pk>/add-skill/', views.add_skill, name='add_skill'),
    path('education/<int:pk>/delete/', views.delete_education, name='delete_education'),
    path('experience/<int:pk>/delete/', views.delete_experience, name='delete_experience'),
    path('skill/<int:pk>/delete/', views.delete_skill, name='delete_skill'),
    
    # Дополнительные маршруты
    path('stats/', views.cv_stats, name='cv_stats'),
    path('template/<int:template_id>/preview/', views.template_preview, name='template_preview'),
]