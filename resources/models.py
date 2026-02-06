from django.contrib.auth import get_user_model
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class ResourceCategory(models.Model):
    """Represents categories for organizing educational resources"""

    name = models.CharField(
        max_length=100,
        verbose_name=_("Category Name"),
        help_text=_("Name of the resource category")
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("Description"),
        help_text=_("Optional description of the category")
    )

    class Meta:
        verbose_name = _("Resource Category")
        verbose_name_plural = _("Resource Categories")
        ordering = ["name"]

    def __str__(self):
        return self.name

    def resource_count(self):
        """Returns count of published resources in this category"""
        return self.resources.filter(is_published=True).count()


class Resource(models.Model):
    """Stores educational resources with optional media content"""

    title = models.CharField(
        max_length=200,
        verbose_name=_("Title"),
        help_text=_("Title of the educational resource")
    )
    category = models.ForeignKey(
        ResourceCategory,
        on_delete=models.SET_NULL,
        null=True,
        related_name="resources",
        verbose_name=_("Category"),
        help_text=_("Category this resource belongs to")
    )
    description = models.TextField(
        verbose_name=_("Description"),
        help_text=_("Detailed description of the resource content")
    )
    image = models.ImageField(
        upload_to="resources/images/%Y/%m/%d/",
        null=True,
        blank=True,
        verbose_name=_("Image"),
        help_text=_("Optional image representing the resource")
    )
    url_youtube = models.URLField(
        blank=True,
        verbose_name=_("YouTube URL"),
        help_text=_("YouTube video URL if applicable")
    )

    # Publication Status
    is_published = models.BooleanField(
        default=False,
        verbose_name=_("Published"),
        help_text=_("Whether this resource is publicly visible")
    )

    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created At")
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Updated At")
    )

    class Meta:
        verbose_name = _("Resource")
        verbose_name_plural = _("Resources")
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("resources:resource_detail", kwargs={"pk": self.pk})

    def has_youtube_video(self):
        return bool(self.url_youtube)
