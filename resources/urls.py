from django.urls import path
from . import views

app_name = 'resources'

urlpatterns = [
    # Public URLs
    path('', views.resource_list, name='list'),
    path('<int:pk>/', views.resource_detail, name='resource_detail'),
    
    # Management URLs
    path('create/', views.resource_create, name='resource_create'),
    path('<int:pk>/edit/', views.resource_edit, name='resource_edit'),
    path('<int:pk>/delete/', views.resource_delete, name='resource_delete'),
    
    # Moderation URLs
    path('unpublished/', views.unpublished_resources, name='unpublished_resources'),
    path('<int:pk>/publish/', views.publish_resource, name='publish_resource'),
    path('<int:pk>/unpublish/', views.unpublish_resource, name='unpublish_resource'),
]