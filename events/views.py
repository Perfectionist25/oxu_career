import base64
import uuid

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db.models import Case, Count, IntegerField, Prefetch, Q, Value, When
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.generic import ListView

from accounts.models import Notification, user_has_admin_permission

from .forms import EventAttendanceScanForm, EventCategoryForm, EventForm
from .models import Event, EventCategory, EventParticipation
from .utils import (
    extract_token_from_payload,
    generate_qr_png_bytes,
    get_check_in_participation_or_404,
)


def _can_manage_events(user):
    return bool(
        user
        and user.is_authenticated
        and (
            user.is_staff
            or user.is_superuser
            or user_has_admin_permission(user, "can_manage_events")
        )
    )


def admin_required(function=None):
    actual_decorator = user_passes_test(
        lambda u: u.is_active and _can_manage_events(u),
        login_url="/accounts/admin-login/",
        redirect_field_name=None,
    )
    if function:
        return actual_decorator(function)
    return actual_decorator


def _notify_event_action(user, title, message, related_url=""):
    Notification.objects.create(
        user=user,
        notification_type="event",
        title=title,
        message=message,
        related_url=related_url,
    )


def _admin_event_queryset():
    return Event.objects.select_related("category", "created_by").prefetch_related(
        "allowed_employer_categories"
    )


def _published_event_queryset():
    return Event.objects.filter(status="published").select_related(
        "category", "created_by"
    ).prefetch_related("photos", "allowed_employer_categories")


def event_list(request):
    """List of published events."""
    events = _published_event_queryset()

    search_query = request.GET.get("search", "").strip()
    category_id = request.GET.get("category", "").strip()
    event_type = request.GET.get("type", "").strip()

    if search_query:
        events = events.filter(
            Q(title__icontains=search_query)
            | Q(short_description__icontains=search_query)
            | Q(description__icontains=search_query)
            | Q(location__icontains=search_query)
            | Q(tags__icontains=search_query)
        )

    if category_id.isdigit():
        events = events.filter(category_id=int(category_id))

    valid_event_types = {choice[0] for choice in Event.EVENT_TYPE_CHOICES}
    if event_type in valid_event_types:
        events = events.filter(event_type=event_type)

    now = timezone.now()
    events = events.annotate(
        registered_count=Count(
            "participations",
            filter=Q(participations__status=EventParticipation.STATUS_REGISTERED),
        )
    ).order_by(
        Case(
            When(start_date__gte=now, then=Value(0)),
            default=Value(1),
            output_field=IntegerField(),
        ),
        "start_date",
    )

    paginator = Paginator(events, 12)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "categories": EventCategory.objects.all().order_by("name"),
        "event_types": Event.EVENT_TYPE_CHOICES,
        "search_query": search_query,
        "selected_category": category_id,
        "selected_type": event_type,
        "total_events": events.count(),
        "can_manage_events": _can_manage_events(request.user),
    }
    return render(request, "events/event_list.html", context)


class EventCalendarView(ListView):
    model = Event
    template_name = "events/event_calendar.html"
    context_object_name = "events"

    def get_queryset(self):
        return _published_event_queryset()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now()
        published_events = Event.objects.filter(status="published")
        context.update(
            {
                "categories": EventCategory.objects.all(),
                "stats_calendar": {
                    "total_events": published_events.count(),
                    "upcoming_events": published_events.filter(start_date__gte=now).count(),
                    "this_month_events": published_events.filter(
                        start_date__year=now.year,
                        start_date__month=now.month,
                    ).count(),
                },
                "upcoming_events": published_events.filter(start_date__gte=now).count(),
                "this_month_events": published_events.filter(
                    start_date__year=now.year,
                    start_date__month=now.month,
                ).count(),
                "can_manage_events": _can_manage_events(self.request.user),
            }
        )
        return context


def event_categories(request):
    return render(request, "events/categories.html", {"categories": EventCategory.objects.all()})


def event_detail(request, slug):
    event = get_object_or_404(_published_event_queryset(), slug=slug)

    session_key = f"event_viewed_{event.id}"
    if not request.session.get(session_key):
        event.views_count += 1
        event.save(update_fields=["views_count"])
        request.session[session_key] = True
        request.session.set_expiry(86400)

    user_participation = None
    participation_error = ""
    if request.user.is_authenticated:
        user_participation = event.get_user_participation(request.user)
        participation_error = event.get_participation_error(request.user)

    context = {
        "event": event,
        "is_admin": _can_manage_events(request.user),
        "user_participation": user_participation,
        "participation_error": participation_error,
        "can_participate": event.can_user_participate(request.user) if request.user.is_authenticated else False,
        "seats_occupied": event.seats_occupied,
        "seats_remaining": event.seats_remaining,
        "allowed_employer_categories": event.employer_category_names(),
    }
    return render(request, "events/detail.html", context)


@login_required
def join_event(request, slug):
    if request.method != "POST":
        return redirect("events:event_detail", slug=slug)

    event = get_object_or_404(_published_event_queryset(), slug=slug)
    error_message = event.get_participation_error(request.user)

    existing_participation = event.get_user_participation(request.user)
    if existing_participation and existing_participation.status == EventParticipation.STATUS_CANCELLED:
        error_message = "" if event.can_user_participate(request.user) else error_message

    if error_message:
        messages.error(request, error_message)
        return redirect("events:event_detail", slug=slug)

    role = event.get_registration_role(request.user)
    if not role:
        messages.error(request, _("Your account is not eligible to register for events."))
        return redirect("events:event_detail", slug=slug)

    participation = existing_participation
    if participation and participation.status == EventParticipation.STATUS_CANCELLED:
        participation.status = EventParticipation.STATUS_REGISTERED
        participation.attendance_status = EventParticipation.ATTENDANCE_REGISTERED
        participation.cancelled_at = None
        participation.checked_in_at = None
        participation.checked_in_by = None
        participation.role = role
        participation.qr_token = uuid.uuid4()
        participation.attendance_code = EventParticipation._generate_attendance_code()
        participation.save()
    elif participation:
        messages.info(request, _("You are already registered for this event."))
        return redirect("events:event_detail", slug=slug)
    else:
        participation = EventParticipation.objects.create(
            event=event,
            user=request.user,
            role=role,
        )

    _notify_event_action(
        request.user,
        _("Event registration confirmed"),
        _("You have successfully registered for %(event)s.") % {"event": event.title},
        related_url=request.build_absolute_uri(
            reverse("events:participation_pass", kwargs={"pk": participation.pk})
        ),
    )
    messages.success(request, _("You have successfully registered for this event."))
    return redirect("events:event_detail", slug=slug)


@login_required
def cancel_registration(request, slug):
    if request.method != "POST":
        return redirect("events:event_detail", slug=slug)

    event = get_object_or_404(_published_event_queryset(), slug=slug)
    participation = get_object_or_404(event.participations, user=request.user)

    try:
        participation.cancel()
    except ValidationError as exc:
        messages.error(request, exc.message)
        return redirect("events:event_detail", slug=slug)

    _notify_event_action(
        request.user,
        _("Event registration cancelled"),
        _("Your participation in %(event)s has been cancelled.") % {"event": event.title},
        related_url=request.build_absolute_uri(event.get_absolute_url()),
    )
    messages.success(request, _("Your participation has been cancelled."))
    return redirect("events:event_detail", slug=slug)


@login_required
def participation_pass(request, pk):
    participation = get_object_or_404(
        EventParticipation.objects.select_related("event", "user"), pk=pk
    )
    if participation.user != request.user and not _can_manage_events(request.user):
        messages.error(request, _("Access denied."))
        return redirect("events:event_list")

    qr_image_data = ""
    qr_generation_error = ""
    if participation.status == EventParticipation.STATUS_REGISTERED:
        try:
            qr_image_data = base64.b64encode(
                generate_qr_png_bytes(participation.attendance_code)
            ).decode("ascii")
        except RuntimeError:
            qr_generation_error = _("QR generation is unavailable because the required package is not installed on the server.")

    context = {
        "participation": participation,
        "event": participation.event,
        "attendance_status": participation.get_effective_attendance_status_display(),
        "qr_image_data": qr_image_data,
        "qr_generation_error": qr_generation_error,
        "attendance_code": participation.attendance_code,
    }
    return render(request, "events/participation_pass.html", context)


@login_required
def participation_qr_image(request, pk):
    participation = get_object_or_404(
        EventParticipation.objects.select_related("event", "user"), pk=pk
    )
    if participation.user != request.user and not _can_manage_events(request.user):
        messages.error(request, _("Access denied."))
        return redirect("events:event_list")

    try:
        png_bytes = generate_qr_png_bytes(participation.attendance_code)
    except RuntimeError:
        return HttpResponse(
            _("QR generation is unavailable because the required package is not installed on the server."),
            status=503,
            content_type="text/plain; charset=utf-8",
        )
    return HttpResponse(png_bytes, content_type="image/png")


@login_required
def my_events(request):
    participations = EventParticipation.objects.filter(user=request.user).select_related(
        "event"
    )

    status_filter = request.GET.get("status", "").strip()
    attendance_filter = request.GET.get("attendance", "").strip()

    if status_filter in {choice[0] for choice in EventParticipation.STATUS_CHOICES}:
        participations = participations.filter(status=status_filter)

    now = timezone.now()
    if attendance_filter == EventParticipation.ATTENDANCE_ATTENDED:
        participations = participations.filter(
            attendance_status=EventParticipation.ATTENDANCE_ATTENDED
        )
    elif attendance_filter == EventParticipation.ATTENDANCE_ABSENT:
        participations = participations.filter(
            status=EventParticipation.STATUS_REGISTERED,
            attendance_status=EventParticipation.ATTENDANCE_REGISTERED,
            event__end_date__lt=now,
        )
    elif attendance_filter == EventParticipation.ATTENDANCE_REGISTERED:
        participations = participations.filter(
            status=EventParticipation.STATUS_REGISTERED,
            attendance_status=EventParticipation.ATTENDANCE_REGISTERED,
            event__end_date__gte=now,
        )

    participations = participations.order_by("-registered_at")
    paginator = Paginator(participations, 10)
    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "page_obj": page_obj,
        "total_events": participations.count(),
        "registration_statuses": EventParticipation.STATUS_CHOICES,
        "attendance_statuses": EventParticipation.ATTENDANCE_STATUS_CHOICES,
    }
    return render(request, "events/my_events.html", context)


@login_required
def manage_events(request):
    if not request.user.is_staff:
        messages.error(request, _("Access denied."))
        return redirect("events:event_list")

    events = Event.objects.all().order_by("-created_at")
    return render(
        request,
        "events/manage_events.html",
        {"events": events, "title": _("Manage Events")},
    )


@login_required
def create_event(request):
    if not request.user.is_staff:
        messages.error(request, _("You don't have permission to create events."))
        return redirect("events:event_list")

    if request.method == "POST":
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            event = form.save(commit=False)
            event.created_by = request.user
            event.status = "published"
            event.save()
            form.save_m2m()
            messages.success(request, _("Event created successfully!"))
            return redirect("events:event_detail", slug=event.slug)
    else:
        form = EventForm()

    return render(request, "events/create_event.html", {"form": form, "title": _("Create Event")})


@login_required
def edit_event(request, slug):
    event = get_object_or_404(Event, slug=slug)
    if not (request.user == event.created_by or request.user.is_staff or request.user.is_superuser):
        messages.error(request, _("You don't have permission to edit this event."))
        return redirect("events:event_detail", slug=slug)

    if request.method == "POST":
        form = EventForm(request.POST, request.FILES, instance=event)
        if form.is_valid():
            form.save()
            messages.success(request, _("Event updated successfully!"))
            return redirect("events:event_detail", slug=event.slug)
    else:
        form = EventForm(instance=event)

    return render(
        request,
        "events/create_event.html",
        {"form": form, "event": event, "title": _("Edit Event")},
    )


@login_required
def delete_event(request, slug):
    event = get_object_or_404(Event, slug=slug)
    if not (request.user == event.created_by or request.user.is_staff or request.user.is_superuser):
        messages.error(request, _("You don't have permission to delete this event."))
        return redirect("events:event_detail", slug=slug)

    if request.method == "POST":
        event.delete()
        messages.success(request, _("Event deleted successfully!"))
        return redirect("events:event_list")

    return render(request, "events/event_delete.html", {"event": event})


@login_required
@admin_required
def admin_event_list(request):
    events = _admin_event_queryset().annotate(
        participant_count=Count(
            "participations",
            filter=Q(participations__status=EventParticipation.STATUS_REGISTERED),
        )
    )

    status_filter = request.GET.get("status")
    category_filter = request.GET.get("category")
    search_query = request.GET.get("search", "")

    if status_filter:
        events = events.filter(status=status_filter)
    if category_filter:
        events = events.filter(category_id=category_filter)
    if search_query:
        events = events.filter(
            Q(title__icontains=search_query)
            | Q(description__icontains=search_query)
            | Q(location__icontains=search_query)
        )

    events = events.order_by(request.GET.get("sort", "-created_at"))

    paginator = Paginator(events, 20)
    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "page_obj": page_obj,
        "categories": EventCategory.objects.all(),
        "search_query": search_query,
        "stats": {
            "total": Event.objects.count(),
            "published": Event.objects.filter(status="published").count(),
            "draft": Event.objects.filter(status="draft").count(),
        },
    }
    return render(request, "events/admin_event_list.html", context)


@login_required
@admin_required
def admin_event_create(request):
    if request.method == "POST":
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            event = form.save(commit=False)
            if not event.created_by:
                event.created_by = request.user
            event.save()
            form.save_m2m()
            messages.success(request, _("Event created successfully!"))
            return redirect("events:admin_event_edit", pk=event.pk)
    else:
        form = EventForm()

    return render(request, "events/admin_event_form.html", {"form": form, "title": _("Create Event")})


@login_required
@admin_required
def admin_event_edit(request, pk):
    event = get_object_or_404(Event, pk=pk)

    if request.method == "POST":
        form = EventForm(request.POST, request.FILES, instance=event)
        if form.is_valid():
            form.save()
            messages.success(request, _("Event updated successfully!"))
            return redirect("events:admin_event_list")
    else:
        form = EventForm(instance=event)

    return render(
        request,
        "events/admin_event_form.html",
        {"form": form, "event": event, "title": _("Edit Event")},
    )


@login_required
@admin_required
def admin_event_delete(request, pk):
    event = get_object_or_404(Event, pk=pk)
    if request.method == "POST":
        event.delete()
        messages.success(request, _("Event deleted successfully!"))
        return redirect("events:admin_event_list")
    return render(request, "events/admin_event_delete.html", {"event": event})


@login_required
@admin_required
def admin_event_publish(request, pk):
    event = get_object_or_404(Event, pk=pk)
    if request.method == "POST":
        event.status = "published"
        event.save(update_fields=["status", "updated_at"])
        messages.success(request, _("Event published successfully!"))
    return redirect("events:admin_event_list")


@login_required
@admin_required
def admin_event_unpublish(request, pk):
    event = get_object_or_404(Event, pk=pk)
    if request.method == "POST":
        event.status = "draft"
        event.save(update_fields=["status", "updated_at"])
        messages.success(request, _("Event unpublished successfully!"))
    return redirect("events:admin_event_list")


@login_required
@admin_required
def admin_event_participants(request, pk):
    event = get_object_or_404(
        _admin_event_queryset().prefetch_related(
            Prefetch(
                "participations",
                queryset=EventParticipation.objects.select_related("user", "checked_in_by"),
            )
        ),
        pk=pk,
    )
    participations = event.participations.select_related("user", "checked_in_by").order_by(
        "-registered_at"
    )

    role_filter = request.GET.get("role", "").strip()
    attendance_filter = request.GET.get("attendance", "").strip()
    now = timezone.now()

    if role_filter in {choice[0] for choice in EventParticipation.ROLE_CHOICES}:
        participations = participations.filter(role=role_filter)

    if attendance_filter == EventParticipation.ATTENDANCE_ATTENDED:
        participations = participations.filter(
            attendance_status=EventParticipation.ATTENDANCE_ATTENDED
        )
    elif attendance_filter == EventParticipation.ATTENDANCE_REGISTERED:
        participations = participations.filter(
            status=EventParticipation.STATUS_REGISTERED,
            attendance_status=EventParticipation.ATTENDANCE_REGISTERED,
            event__end_date__gte=now,
        )
    elif attendance_filter == EventParticipation.ATTENDANCE_ABSENT:
        participations = participations.filter(
            status=EventParticipation.STATUS_REGISTERED,
            attendance_status=EventParticipation.ATTENDANCE_REGISTERED,
            event__end_date__lt=now,
        )
    elif attendance_filter == EventParticipation.STATUS_CANCELLED:
        participations = participations.filter(status=EventParticipation.STATUS_CANCELLED)

    paginator = Paginator(participations, 25)
    page_obj = paginator.get_page(request.GET.get("page"))

    base_queryset = event.participations.all()
    context = {
        "event": event,
        "page_obj": page_obj,
        "role_choices": EventParticipation.ROLE_CHOICES,
        "attendance_choices": [
            (EventParticipation.ATTENDANCE_REGISTERED, _("Registered")),
            (EventParticipation.ATTENDANCE_ATTENDED, _("Attended")),
            (EventParticipation.ATTENDANCE_ABSENT, _("Absent")),
            (EventParticipation.STATUS_CANCELLED, _("Cancelled")),
        ],
        "stats": {
            "total": base_queryset.count(),
            "registered": base_queryset.filter(status=EventParticipation.STATUS_REGISTERED).count(),
            "attended": base_queryset.filter(
                attendance_status=EventParticipation.ATTENDANCE_ATTENDED
            ).count(),
            "absent": base_queryset.filter(
                status=EventParticipation.STATUS_REGISTERED,
                attendance_status=EventParticipation.ATTENDANCE_REGISTERED,
                event__end_date__lt=now,
            ).count(),
            "students": base_queryset.filter(role=EventParticipation.ROLE_STUDENT).count(),
            "employers": base_queryset.filter(role=EventParticipation.ROLE_EMPLOYER).count(),
        },
        "scan_form": EventAttendanceScanForm(),
    }
    return render(request, "events/admin_event_participants.html", context)


@login_required
@admin_required
def admin_event_check_in(request, pk):
    event = get_object_or_404(_admin_event_queryset(), pk=pk)
    form = EventAttendanceScanForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        try:
            token = extract_token_from_payload(form.cleaned_data["qr_payload"])
        except ValidationError as exc:
            messages.error(request, exc.message)
        else:
            participation = get_check_in_participation_or_404(event, token)
            try:
                participation.mark_attended(checked_in_by=request.user)
            except ValidationError as exc:
                messages.error(request, exc.message)
            else:
                _notify_event_action(
                    participation.user,
                    _("Attendance confirmed"),
                    _("Your attendance for %(event)s has been confirmed.") % {"event": event.title},
                    related_url=request.build_absolute_uri(
                        reverse("events:participation_pass", kwargs={"pk": participation.pk})
                    ),
                )
                messages.success(
                    request,
                    _("Attendance confirmed for %(name)s.") % {"name": participation.user.get_full_name()},
                )
            return redirect("events:admin_event_check_in", pk=event.pk)

    recent_attendees = event.participations.filter(
        attendance_status=EventParticipation.ATTENDANCE_ATTENDED
    ).select_related("user", "checked_in_by").order_by("-checked_in_at")[:10]

    return render(
        request,
        "events/admin_event_check_in.html",
        {
            "event": event,
            "form": form,
            "recent_attendees": recent_attendees,
        },
    )


@login_required
@admin_required
def admin_event_check_in_token(request, pk, token):
    event = get_object_or_404(_admin_event_queryset(), pk=pk)
    participation = get_check_in_participation_or_404(event, token)

    try:
        participation.mark_attended(checked_in_by=request.user)
    except ValidationError as exc:
        messages.error(request, exc.message)
    else:
        _notify_event_action(
            participation.user,
            _("Attendance confirmed"),
            _("Your attendance for %(event)s has been confirmed.") % {"event": event.title},
            related_url=request.build_absolute_uri(
                reverse("events:participation_pass", kwargs={"pk": participation.pk})
            ),
        )
        messages.success(
            request,
            _("Attendance confirmed for %(name)s.") % {"name": participation.user.get_full_name()},
        )

    return redirect("events:admin_event_check_in", pk=event.pk)


@login_required
@admin_required
def admin_category_list(request):
    return render(
        request,
        "events/admin_category_list.html",
        {"categories": EventCategory.objects.all()},
    )


@login_required
@admin_required
def admin_category_create(request):
    if request.method == "POST":
        form = EventCategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _("Category created successfully!"))
            return redirect("events:admin_category_list")
    else:
        form = EventCategoryForm()

    return render(request, "events/admin_category_form.html", {"form": form, "title": _("Create Category")})


@login_required
@admin_required
def admin_category_edit(request, pk):
    category = get_object_or_404(EventCategory, pk=pk)
    if request.method == "POST":
        form = EventCategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, _("Category updated successfully!"))
            return redirect("events:admin_category_list")
    else:
        form = EventCategoryForm(instance=category)

    return render(
        request,
        "events/admin_category_form.html",
        {"form": form, "category": category, "title": _("Edit Category")},
    )


@login_required
@admin_required
def admin_category_delete(request, pk):
    category = get_object_or_404(EventCategory, pk=pk)
    if request.method == "POST":
        category.delete()
        messages.success(request, _("Category deleted successfully!"))
        return redirect("events:admin_category_list")
    return render(request, "events/admin_category_delete.html", {"category": category})


def api_events(request):
    events = _published_event_queryset()
    start = request.GET.get("start")
    end = request.GET.get("end")
    category = request.GET.get("category")

    if start and end:
        try:
            start_date = timezone.datetime.fromisoformat(start)
            end_date = timezone.datetime.fromisoformat(end)
            events = events.filter(start_date__gte=start_date, start_date__lte=end_date)
        except ValueError:
            pass

    if category:
        events = events.filter(category_id=category)

    data = []
    for event in events:
        data.append(
            {
                "id": event.id,
                "title": event.title,
                "start": event.start_date.isoformat(),
                "end": event.end_date.isoformat() if event.end_date else None,
                "url": reverse("events:event_detail", kwargs={"slug": event.slug}),
                "color": event.category.color if event.category else "#667eea",
                "location": event.location,
                "category": event.category.name if event.category else _("Other"),
            }
        )

    return JsonResponse(data, safe=False)


def api_event_stats(request):
    if not _can_manage_events(request.user):
        return JsonResponse({"error": "Unauthorized"}, status=403)

    from django.db.models.functions import TruncMonth

    monthly_stats = (
        Event.objects.filter(created_at__year=timezone.now().year)
        .annotate(month=TruncMonth("created_at"))
        .values("month")
        .annotate(count=Count("id"))
        .order_by("month")
    )

    data = {
        "total": Event.objects.count(),
        "upcoming_events": Event.objects.filter(start_date__gte=timezone.now()).count(),
        "this_month_events": Event.objects.filter(start_date__month=timezone.now().month).count(),
        "published": Event.objects.filter(status="published").count(),
        "draft": Event.objects.filter(status="draft").count(),
        "monthly_stats": list(monthly_stats),
    }
    return JsonResponse(data)


def stats_calendar(request):
    context = {
        "events": Event.objects.filter(status="published").count(),
        "upcoming_events": Event.objects.filter(start_date__gte=timezone.now()).count(),
        "this_month_events": Event.objects.filter(
            start_date__year=timezone.now().year,
            start_date__month=timezone.now().month,
        ).count(),
    }
    return render(request, "events/stats_calendar.html", context)
