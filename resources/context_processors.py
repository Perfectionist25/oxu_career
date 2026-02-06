from typing import Any, Dict

from django.db import models
from django.db.models import Count

from .models import Resource, ResourceCategory


def resources_context(request):
    """
    Context processor для ресурсов - добавляет данные во все шаблоны
    """
    context: Dict[str, Any] = {}

    try:
        # Категории ресурсов с количеством опубликованных ресурсов
        categories = (
            ResourceCategory.objects.annotate(
                published_resources_count=Count(
                    "resources", filter=models.Q(resources__is_published=True)
                )
            )
            .filter(published_resources_count__gt=0)
            .order_by("name")
        )

        context["resource_categories"] = categories

        # Популярные/рекомендуемые ресурсы (последние 5 опубликованных)
        featured_resources = (
            Resource.objects.filter(is_published=True)
            .select_related("category")
            .order_by("-created_at")[:5]
        )

        context["featured_resources"] = featured_resources

        # Общая статистика ресурсов
        total_resources = Resource.objects.filter(is_published=True).count()
        total_categories = ResourceCategory.objects.count()

        context["resources_stats"] = {
            "total_resources": total_resources,
            "total_categories": total_categories,
        }

    except Exception:
        # Если база данных еще не готова или другие ошибки
        # Возвращаем QuerySet.none() чтобы сохранить согласованность типов
        context.update(
            {
                "resource_categories": ResourceCategory.objects.none(),
                "featured_resources": Resource.objects.none(),
                "resources_stats": {
                    "total_resources": 0,
                    "total_categories": 0,
                },
            }
        )

    return context


def resources_admin_context(request):
    """
    Context processor для админ-раздела ресурсов
    """
    context: Dict[str, Any] = {}

    if request.user.is_authenticated and request.user.is_staff:
        try:
            # Статистика для админов
            unpublished_count = Resource.objects.filter(is_published=False).count()
            total_resources = Resource.objects.count()

            context["resources_admin_stats"] = {
                "unpublished_count": unpublished_count,
                "total_resources": total_resources,
                "approval_needed": unpublished_count > 0,
            }
        except Exception:
            context["resources_admin_stats"] = {
                "unpublished_count": 0,
                "total_resources": 0,
                "approval_needed": False,
            }

    return context


def resources_navigation_context(request):
    """
    Context processor для навигации по ресурсам
    """
    context: Dict[str, Any] = {}

    try:
        # Категории для главного меню (только с опубликованными ресурсами)
        nav_categories = (
            ResourceCategory.objects.annotate(
                published_resources_count=Count(
                    "resources", filter=models.Q(resources__is_published=True)
                )
            )
            .filter(published_resources_count__gt=0)
            .order_by("name")[:8]
        )  # Ограничиваем для меню

        context["nav_resource_categories"] = nav_categories

        # Быстрые ссылки для футера
        recent_resources = (
            Resource.objects.filter(is_published=True)
            .select_related("category")
            .order_by("-created_at")[:3]
        )

        context["recent_resources"] = recent_resources

    except Exception:
        context.update(
            {
                "nav_resource_categories": ResourceCategory.objects.none(),
                "recent_resources": Resource.objects.none(),
            }
        )

    return context
