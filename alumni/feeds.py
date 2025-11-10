from django.contrib.syndication.views import Feed
from django.urls import reverse
from django.utils.feedgenerator import Rss201rev2Feed
from django.utils.translation import gettext_lazy as _

from .models import Event, Job, News


class ExtendedRSSFeed(Rss201rev2Feed):
    """Расширенный RSS feed с дополнительными полями"""

    def add_item_elements(self, handler, item):
        super().add_item_elements(handler, item)
        if item["author"] is not None:
            handler.addQuickElement("author", item["author"])
        if item["image"] is not None:
            handler.addQuickElement("image", item["image"])


class LatestNewsFeed(Feed):
    """RSS feed для последних новостей"""

    title = _("OXU Alumni - So'ngi yangiliklar")
    link = "/alumni/news/"
    description = _("OXU bitiruvchilari assotsiatsiyasining so'ngi yangiliklari")
    feed_type = ExtendedRSSFeed

    def items(self):
        return News.objects.filter(is_published=True).order_by("-created_at")[:20]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        # Ограничиваем длину описания для RSS
        content = item.content
        if len(content) > 300:
            return content[:300] + "..."
        return content

    def item_link(self, item):
        return reverse("alumni:news_detail", kwargs={"slug": item.slug})

    def item_author_name(self, item):
        return item.author.name if item.author else "OXU Alumni"

    def item_pubdate(self, item):
        return item.created_at

    def item_extra_kwargs(self, item):
        return {
            "author": item.author.name if item.author else None,
            "image": item.image.url if item.image else None,
        }


class LatestJobsFeed(Feed):
    """RSS feed для последних вакансий"""

    title = _("OXU Alumni - So'ngi vakansiyalar")
    link = "/alumni/jobs/"
    description = _("OXU bitiruvchilari uchun so'ngi ish vakansiyalari")
    feed_type = ExtendedRSSFeed

    def items(self):
        return Job.objects.filter(is_active=True).order_by("-created_at")[:25]

    def item_title(self, item):
        return f"{item.title} - {item.company.name}"

    def item_description(self, item):
        desc = f"Kompaniya: {item.company.name}\n"
        desc += f"Lavozim: {item.title}\n"
        desc += f"Manzil: {item.location}\n"
        desc += f"Ish turi: {item.get_employment_type_display()}\n\n"

        if item.salary_min and item.salary_max:
            desc += f"Maosh: {item.salary_min} - {item.salary_max} {item.currency}\n"

        desc += (
            f"\n{item.description[:200]}..."
            if len(item.description) > 200
            else f"\n{item.description}"
        )
        return desc

    def item_link(self, item):
        return reverse("alumni:job_detail", kwargs={"pk": item.pk})

    def item_author_name(self, item):
        return item.company.name

    def item_pubdate(self, item):
        return item.created_at

    def item_extra_kwargs(self, item):
        return {
            "author": item.company.name,
            "image": item.company.logo.url if item.company.logo else None,
        }


class UpcomingEventsFeed(Feed):
    """RSS feed для предстоящих мероприятий"""

    title = _("OXU Alumni - Kelgusi tadbirlar")
    link = "/alumni/events/"
    description = _("OXU bitiruvchilari uchun kelgusi tadbirlar")
    feed_type = ExtendedRSSFeed

    def items(self):
        from datetime import date

        return (
            Event.objects.filter(is_active=True, date__gte=date.today())
            .order_by("date")[:15]
        )

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        desc = f"Tadbir turi: {item.get_event_type_display()}\n"
        desc += f"Sana: {item.date}\n"
        desc += f"Vaqt: {item.time}\n"
        desc += f"Manzil: {item.location}\n\n"
        desc += (
            f"{item.description[:250]}..."
            if len(item.description) > 250
            else item.description
        )
        return desc

    def item_link(self, item):
        return reverse("alumni:event_detail", kwargs={"pk": item.pk})

    def item_author_name(self, item):
        return item.organizer.name if item.organizer else "OXU Alumni"

    def item_pubdate(self, item):
        return item.created_at

    def item_extra_kwargs(self, item):
        return {
            "author": item.organizer.name if item.organizer else None,
        }


class AllUpdatesFeed(Feed):
    """Общий RSS feed всех обновлений"""

    title = _("OXU Alumni - Barcha yangilanishlar")
    link = "/alumni/"
    description = _("OXU bitiruvchilari portalidagi barcha yangilanishlar")

    def items(self):
        # Объединяем новости, вакансии и мероприятия
        from itertools import chain
        from datetime import datetime

        news = News.objects.filter(is_published=True).order_by("-created_at")[:10]
        jobs = Job.objects.filter(is_active=True).order_by("-created_at")[:10]
        events = Event.objects.filter(is_active=True).order_by("-created_at")[:10]

        # Сортируем все по дате создания. Use getattr to avoid mypy complaining
        # about missing 'created_at' on the union of different model types.
        # Use a datetime fallback so the key is always comparable
        all_items = sorted(
            chain(news, jobs, events),
            key=lambda x: getattr(x, "created_at", datetime.min),
            reverse=True,
        )[:20]

        return all_items

    def item_title(self, item):
        if hasattr(item, "content"):  # News
            return f"📰 {item.title}"
        elif hasattr(item, "description"):  # Job
            return f"💼 {item.title} - {item.company.name}"
        elif hasattr(item, "event_type"):  # Event
            return f"🎯 {item.title}"
        return item.title

    def item_description(self, item):
        if hasattr(item, "content"):  # News
            content = item.content
            return content[:300] + "..." if len(content) > 300 else content
        elif hasattr(item, "description"):  # Job
            return (
                f"{item.description[:200]}..."
                if len(item.description) > 200
                else item.description
            )
        elif hasattr(item, "event_type"):  # Event
            return (
                f"{item.description[:200]}..."
                if len(item.description) > 200
                else item.description
            )
        return ""

    def item_link(self, item):
        if hasattr(item, "content"):  # News
            return reverse("alumni:news_detail", kwargs={"slug": item.slug})
        elif hasattr(item, "description"):  # Job
            return reverse("alumni:job_detail", kwargs={"pk": item.pk})
        elif hasattr(item, "event_type"):  # Event
            return reverse("alumni:event_detail", kwargs={"pk": item.pk})
        return "/alumni/"

    def item_pubdate(self, item):
        return item.created_at
