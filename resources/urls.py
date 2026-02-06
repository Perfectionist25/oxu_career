from django.urls import path
from . import views

app_name = "resources"

urlpatterns = [
    # Public URLs
    path("", views.resource_list, name="list"),
    path("<int:pk>/", views.resource_detail, name="resource_detail"),
    path("<int:pk>/view/", views.resource_detail, name="resource_detail"),  # Альтернатива для ясности
    
    # CRUD URLs
    path("create/", views.resource_create, name="resource_create"),
    path("<int:pk>/edit/", views.resource_edit, name="resource_edit"),
    path("<int:pk>/update/", views.resource_edit, name="resource_update"),  # Альтернатива
    path("<int:pk>/delete/", views.resource_delete, name="resource_delete"),
    
    # Moderation URLs - сгруппированы
    path("moderation/unpublished/", views.unpublished_resources, name="unpublished_resources"),
    path("moderation/<int:pk>/publish/", views.publish_resource, name="publish_resource"),
    path("moderation/<int:pk>/unpublish/", views.unpublish_resource, name="unpublish_resource"),
    path("moderation/bulk-publish/", views.bulk_publish_resources, name="bulk_publish"),
    path("moderation/bulk-delete/", views.bulk_delete_resources, name="bulk_delete"),
    
    # Bulk Actions
    path('bulk/publish/', views.bulk_publish_resources, name='bulk_publish'),
    path('bulk/delete/', views.bulk_delete_resources, name='bulk_delete'),
    path('bulk/archive/', views.bulk_archive_resources, name='bulk_archive'),
    path('bulk/action/', views.bulk_action_api, name='bulk_action_api'),
    path('stats/unpublished/', views.unpublished_resources_stats, name='unpublished_stats'),
]