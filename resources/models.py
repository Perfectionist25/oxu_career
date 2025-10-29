from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth import get_user_model
User = get_user_model()

class ResourceCategory(models.Model):
    """Категории ресурсов"""
    name = models.CharField(max_length=100, verbose_name=_("Category Name"))
    description = models.TextField(blank=True, verbose_name=_("Description"))
    icon = models.CharField(max_length=50, blank=True, verbose_name=_("Icon"))
    color = models.CharField(max_length=7, default='#007cba', verbose_name=_("Color"))
    order = models.IntegerField(default=0, verbose_name=_("Display Order"))
    
    class Meta:
        verbose_name = _("Resource Category")
        verbose_name_plural = _("Resource Categories")
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

    def resource_count(self):
        return self.resources.filter(is_published=True).count()

class Resource(models.Model):
    """Образовательные ресурсы"""
    RESOURCE_TYPE_CHOICES = [
        ('article', _('Article')),
        ('tutorial', _('Tutorial')),
        ('video', _('Video')),
        ('ebook', _('E-book')),
        ('course', _('Online Course')),
        ('tool', _('Tool/Software')),
        ('template', _('Template')),
        ('cheatsheet', _('Cheat Sheet')),
        ('guide', _('Guide')),
        ('other', _('Other')),
    ]
    
    LEVEL_CHOICES = [
        ('beginner', _('Beginner')),
        ('intermediate', _('Intermediate')),
        ('advanced', _('Advanced')),
        ('all', _('All Levels')),
    ]
    
    LANGUAGE_CHOICES = [
        ('en', _('English')),
        ('uz', _('Uzbek')),
        ('ru', _('Russian')),
        ('multi', _('Multiple Languages')),
    ]

    # Основная информация
    title = models.CharField(max_length=200, verbose_name=_("Title"))
    description = models.TextField(verbose_name=_("Description"))
    short_description = models.TextField(max_length=300, verbose_name=_("Short Description"))
    category = models.ForeignKey(ResourceCategory, on_delete=models.SET_NULL, null=True, related_name='resources', verbose_name=_("Category"))
    resource_type = models.CharField(max_length=20, choices=RESOURCE_TYPE_CHOICES, verbose_name=_("Resource Type"))
    
    # Контент
    content = models.TextField(blank=True, verbose_name=_("Content"))
    external_url = models.URLField(blank=True, verbose_name=_("External URL"))
    file = models.FileField(upload_to='resources/files/', null=True, blank=True, verbose_name=_("File"))
    thumbnail = models.ImageField(upload_to='resources/thumbnails/', null=True, blank=True, verbose_name=_("Thumbnail"))
    
    # Мета-информация
    author = models.CharField(max_length=100, blank=True, verbose_name=_("Author"))
    publisher = models.CharField(max_length=100, blank=True, verbose_name=_("Publisher"))
    language = models.CharField(max_length=10, choices=LANGUAGE_CHOICES, default='en', verbose_name=_("Language"))
    level = models.CharField(max_length=15, choices=LEVEL_CHOICES, default='all', verbose_name=_("Level"))
    duration = models.CharField(max_length=50, blank=True, help_text=_("e.g., 2 hours, 30 minutes"), verbose_name=_("Duration"))
    
    # Теги и ключевые слова
    tags = models.CharField(max_length=500, blank=True, verbose_name=_("Tags"))
    keywords = models.CharField(max_length=500, blank=True, verbose_name=_("Keywords"))
    
    # Статус и доступ
    is_published = models.BooleanField(default=False, verbose_name=_("Published"))
    is_featured = models.BooleanField(default=False, verbose_name=_("Featured"))
    is_free = models.BooleanField(default=True, verbose_name=_("Free Resource"))
    requires_login = models.BooleanField(default=False, verbose_name=_("Requires Login"))
    
    # Статистика
    views_count = models.IntegerField(default=0, verbose_name=_("Views Count"))
    downloads_count = models.IntegerField(default=0, verbose_name=_("Downloads Count"))
    likes_count = models.IntegerField(default=0, verbose_name=_("Likes Count"))
    
    # SEO
    slug = models.SlugField(unique=True, verbose_name=_("Slug"))
    meta_description = models.TextField(blank=True, verbose_name=_("Meta Description"))
    
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name=_("Created By"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Resource")
        verbose_name_plural = _("Resources")
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('resources:resource_detail', kwargs={'slug': self.slug})

    def is_external(self):
        return bool(self.external_url)

    def is_downloadable(self):
        return bool(self.file)

    def get_file_size(self):
        if self.file and self.file.size:
            size = self.file.size
            if size < 1024:
                return f"{size} B"
            elif size < 1024 * 1024:
                return f"{size / 1024:.1f} KB"
            else:
                return f"{size / (1024 * 1024):.1f} MB"
        return None

class ResourceReview(models.Model):
    """Отзывы о ресурсах"""
    RATING_CHOICES = [
        (1, '1 - Poor'),
        (2, '2 - Fair'),
        (3, '3 - Good'),
        (4, '4 - Very Good'),
        (5, '5 - Excellent'),
    ]

    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, related_name='reviews', verbose_name=_("Resource"))
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name=_("User"))
    
    rating = models.IntegerField(choices=RATING_CHOICES, verbose_name=_("Rating"))
    comment = models.TextField(verbose_name=_("Comment"))
    pros = models.TextField(blank=True, verbose_name=_("Pros"))
    cons = models.TextField(blank=True, verbose_name=_("Cons"))
    
    is_approved = models.BooleanField(default=True, verbose_name=_("Approved"))
    is_verified = models.BooleanField(default=False, verbose_name=_("Verified Review"))
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Resource Review")
        verbose_name_plural = _("Resource Reviews")
        unique_together = ['resource', 'user']
        ordering = ['-created_at']

    def __str__(self):
        return f"Review by {self.user.username} for {self.resource.title}"

class ResourceDownload(models.Model):
    """История загрузок ресурсов"""
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, related_name='downloads', verbose_name=_("Resource"))
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name=_("User"))
    downloaded_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Downloaded At"))
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name=_("IP Address"))
    
    class Meta:
        verbose_name = _("Resource Download")
        verbose_name_plural = _("Resource Downloads")
        ordering = ['-downloaded_at']

    def __str__(self):
        return f"{self.user.username} downloaded {self.resource.title}"

class ResourceLike(models.Model):
    """Лайки ресурсов"""
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, related_name='likes', verbose_name=_("Resource"))
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name=_("User"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Liked At"))
    
    class Meta:
        verbose_name = _("Resource Like")
        verbose_name_plural = _("Resource Likes")
        unique_together = ['resource', 'user']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} liked {self.resource.title}"

class StudyPlan(models.Model):
    """Учебные планы"""
    name = models.CharField(max_length=200, verbose_name=_("Plan Name"))
    description = models.TextField(blank=True, verbose_name=_("Description"))
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='study_plans', verbose_name=_("User"))
    resources = models.ManyToManyField(Resource, through='StudyPlanItem', verbose_name=_("Resources"))
    is_public = models.BooleanField(default=False, verbose_name=_("Public Plan"))
    color = models.CharField(max_length=7, default='#007cba', verbose_name=_("Color"))
    estimated_duration = models.CharField(max_length=50, blank=True, verbose_name=_("Estimated Duration"))
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Study Plan")
        verbose_name_plural = _("Study Plans")
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('resources:study_plan_detail', kwargs={'pk': self.pk})

    def resource_count(self):
        return self.resources.count()

    def total_duration(self):
        # Логика расчета общей продолжительности
        return "Varies"  # Можно реализовать более сложную логику

class StudyPlanItem(models.Model):
    """Элементы учебного плана"""
    study_plan = models.ForeignKey(StudyPlan, on_delete=models.CASCADE, verbose_name=_("Study Plan"))
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, verbose_name=_("Resource"))
    order = models.IntegerField(default=0, verbose_name=_("Order"))
    notes = models.TextField(blank=True, verbose_name=_("Notes"))
    completed = models.BooleanField(default=False, verbose_name=_("Completed"))
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Completed At"))
    
    class Meta:
        verbose_name = _("Study Plan Item")
        verbose_name_plural = _("Study Plan Items")
        ordering = ['order']
        unique_together = ['study_plan', 'resource']

    def __str__(self):
        return f"{self.resource.title} in {self.study_plan.name}"

class CareerPath(models.Model):
    """Карьерные пути"""
    name = models.CharField(max_length=200, verbose_name=_("Career Path Name"))
    description = models.TextField(verbose_name=_("Description"))
    industry = models.CharField(max_length=100, verbose_name=_("Industry"))
    required_skills = models.TextField(help_text=_("List skills separated by commas"), verbose_name=_("Required Skills"))
    average_salary = models.CharField(max_length=100, blank=True, verbose_name=_("Average Salary"))
    growth_outlook = models.CharField(max_length=100, blank=True, verbose_name=_("Growth Outlook"))
    resources = models.ManyToManyField(Resource, blank=True, verbose_name=_("Recommended Resources"))
    is_active = models.BooleanField(default=True, verbose_name=_("Active"))
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Career Path")
        verbose_name_plural = _("Career Paths")
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('resources:career_path_detail', kwargs={'pk': self.pk})

    def resource_count(self):
        return self.resources.count()

class LearningTrack(models.Model):
    """Обучающие треки"""
    name = models.CharField(max_length=200, verbose_name=_("Track Name"))
    description = models.TextField(verbose_name=_("Description"))
    career_path = models.ForeignKey(CareerPath, on_delete=models.CASCADE, related_name='learning_tracks', verbose_name=_("Career Path"))
    level = models.CharField(max_length=15, choices=Resource.LEVEL_CHOICES, verbose_name=_("Level"))
    resources = models.ManyToManyField(Resource, through='TrackResource', verbose_name=_("Resources"))
    estimated_duration = models.CharField(max_length=50, verbose_name=_("Estimated Duration"))
    is_active = models.BooleanField(default=True, verbose_name=_("Active"))
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Learning Track")
        verbose_name_plural = _("Learning Tracks")
        ordering = ['level', 'name']

    def __str__(self):
        return f"{self.name} - {self.get_level_display()}"

    def resource_count(self):
        return self.resources.count()

class TrackResource(models.Model):
    """Ресурсы в обучающих треках"""
    track = models.ForeignKey(LearningTrack, on_delete=models.CASCADE, verbose_name=_("Track"))
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, verbose_name=_("Resource"))
    order = models.IntegerField(default=0, verbose_name=_("Order"))
    is_required = models.BooleanField(default=True, verbose_name=_("Required"))
    
    class Meta:
        verbose_name = _("Track Resource")
        verbose_name_plural = _("Track Resources")
        ordering = ['order']
        unique_together = ['track', 'resource']

    def __str__(self):
        return f"{self.resource.title} in {self.track.name}"