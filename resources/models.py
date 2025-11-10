from django.contrib.auth import get_user_model
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class ResourceCategory(models.Model):
    """Категории ресурсов"""

    name = models.CharField(max_length=100, verbose_name=_("Category Name"))
    description = models.TextField(blank=True, verbose_name=_("Description"))
    # created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Resource Category")
        verbose_name_plural = _("Resource Categories")
        ordering = ["name"]

    def __str__(self):
        return self.name

    def resource_count(self):
        return self.resources.filter(is_published=True).count()


class Resource(models.Model):
    """Образовательные ресурсы"""

    title = models.CharField(max_length=200, verbose_name=_("Title"))
    category = models.ForeignKey(
        ResourceCategory,
        on_delete=models.SET_NULL,
        null=True,
        related_name="resources",
        verbose_name=_("Category"),
    )
    description = models.TextField(verbose_name=_("Description"))
    image = models.ImageField(
        upload_to="resources/images/%Y/%m/%d/",
        null=True,
        blank=True,
        verbose_name=_("Image"),
    )
    url_youtube = models.URLField(blank=True, verbose_name=_("YouTube URL"))

    # Статус публикации
    is_published = models.BooleanField(default=False, verbose_name=_("Published"))

    # Даты
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

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
