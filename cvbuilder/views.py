

from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.views.generic import ListView

from accounts.models import StudentProfile, user_has_admin_permission

from .forms import CVForm, EducationForm, ExperienceForm, SkillForm, LanguageForm
from .models import CV, CVTemplate, Education, Experience, Skill, Language, Project, Certificate

DEFAULT_TEMPLATE_TYPE = "classic"
TEMPLATE_DIR = "cv_render"





def get_student_profile(user):
    """
    Возвращает StudentProfile текущего пользователя или None.
    Работает и для admin, если у него есть student_profile.
    """
    return getattr(user, "student_profile", None)


def is_owner(request_user, cv: CV) -> bool:
    profile = get_student_profile(request_user)
    return bool(profile) and cv.user_id == profile.id


def can_view_cv(user, cv: CV) -> bool:

    if is_owner(user, cv):
        return True

    return cv.status == "published"


def can_access_public_list(user) -> bool:
    if not user or not user.is_authenticated:
        return False

    if getattr(user, "user_type", None) == "employer":
        return True

    return user_has_admin_permission(user, "can_manage_resumes")


def can_export_cv(user, cv: CV) -> bool:

    if is_owner(user, cv):
        return True

    if cv.status != "published":
        return False

    if getattr(user, "user_type", None) == "employer":
        return True

    return user_has_admin_permission(user, "can_manage_resumes")






@login_required
def template_selector(request):
    templates = CVTemplate.objects.filter(is_active=True)
    return render(request, "cvbuilder/template_selector.html", {"templates": templates})






class CVListView(ListView):
    model = CV
    template_name = "cvbuilder/cv_list.html"
    context_object_name = "cvs"

    def get_queryset(self):
        profile = get_student_profile(self.request.user)
        if not profile:
            return CV.objects.none()

        return (
            CV.objects
            .filter(user=profile)
            .select_related("template")
            .prefetch_related("skills", "experiences", "educations", "languages", "projects", "certificates")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cvs = self.object_list

        context.update({
            "published_count": cvs.filter(status="published").count(),
            "draft_count": cvs.filter(status="draft").count(),
            "archived_count": cvs.filter(status="archived").count(),
            "published_cvs": cvs.filter(status="published"),
            "draft_cvs": cvs.filter(status="draft"),
            "archived_cvs": cvs.filter(status="archived"),
            "templates": CVTemplate.objects.filter(is_active=True),
        })
        return context






@login_required
def cv_create(request):
    profile = get_student_profile(request.user)
    if not profile:
        messages.error(request, _("Only users with StudentProfile can create CVs."))
        return redirect("cvbuilder:cv_list")

    if request.method == "POST":
        form = CVForm(request.POST, request.FILES)
        if form.is_valid():
            cv = form.save(commit=False)
            cv.user = profile
            cv.save()
            messages.success(request, _("Resume successfully created!"))
            return redirect("cvbuilder:cv_edit", pk=cv.pk)
        messages.error(request, _("Fill out your resume!"))
    else:
        form = CVForm()

    templates = CVTemplate.objects.filter(is_active=True)
    return render(request, "cvbuilder/cv_create.html", {"form": form, "templates": templates})


@login_required
def cv_edit(request, pk):
    profile = get_student_profile(request.user)
    if not profile:
        messages.error(request, _("You don't have StudentProfile."))
        return redirect("cvbuilder:cv_list")

    cv = get_object_or_404(CV, pk=pk, user=profile)

    if request.method == "POST":
        form = CVForm(request.POST, request.FILES, instance=cv)
        if form.is_valid():
            form.save()
            messages.success(request, _("Rezyume yangilandi!"))
            return redirect("cvbuilder:cv_edit", pk=cv.pk)
    else:
        form = CVForm(instance=cv)

    context = {
        "cv": cv,
        "form": form,
        "education_form": EducationForm(),
        "experience_form": ExperienceForm(),
        "skill_form": SkillForm(),
        "language_form": LanguageForm(),
    }
    return render(request, "cvbuilder/cv_edit.html", context)


@login_required
def cv_detail(request, pk):
    cv = get_object_or_404(
        CV.objects.select_related("template", "user").prefetch_related(
            "skills", "experiences", "educations", "languages", "projects", "certificates"
        ),
        pk=pk
    )

    if not can_view_cv(request.user, cv):
        messages.error(request, _("Sizga ushbu rezyumega kirish huquqi yo'q."))
        return redirect("cvbuilder:cv_list")

    return render(request, "cvbuilder/cv_detail.html", {"cv": cv})


@login_required
def cv_preview(request, pk):
    cv = get_object_or_404(CV, pk=pk)

    template_type = DEFAULT_TEMPLATE_TYPE
    if cv.template and cv.template.template_type:
        template_type = cv.template.template_type

    template_path = f"{TEMPLATE_DIR}/{template_type}.html"

    return render(request, template_path, {
        "cv": cv,
        "template": cv.template,
        "hide_chrome": True,
    })




@login_required
def cv_export_pdf(request, pk):
    cv = get_object_or_404(CV.objects.select_related("template", "user"), pk=pk)

    template_file = getattr(cv.template, "template_file", None)
    if not template_file:
        messages.error(request, _("Selected template is not available."))
        return redirect("cvbuilder:cv_detail", pk=cv.pk)

    if not can_export_cv(request.user, cv):
        messages.error(request, _("Sizda ushbu rezyumeni eksport qilish huquqi yo'q."))
        return redirect("cvbuilder:cv_detail", pk=cv.pk)

    try:
        html_string = render_to_string(f"cvbuilder/{template_file}", {"cv": cv})

        from weasyprint import HTML
        pdf_file = HTML(string=html_string).write_pdf()

        response = HttpResponse(pdf_file, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{cv.title}.pdf"'
        return response

    except ImportError:
        # fallback: render HTML
        return HttpResponse(html_string, content_type="text/html")
    except Exception:
        messages.error(request, _("PDF yaratishda xatolik yuz berdi."))
        return redirect("cvbuilder:cv_detail", pk=cv.pk)


@login_required
def cv_duplicate(request, pk):
    profile = get_student_profile(request.user)
    if not profile:
        messages.error(request, _("You don't have StudentProfile."))
        return redirect("cvbuilder:cv_list")

    original = get_object_or_404(
        CV.objects.prefetch_related("educations", "experiences", "skills", "languages", "projects", "certificates"),
        pk=pk,
        user=profile,
    )


    new_cv = CV.objects.create(
        user=profile,
        title=f"{original.title} (nusxa)",
        template=original.template,
        status="draft",

        full_name=original.full_name,
        email=original.email,
        phone=original.phone,
        phone_secondary=original.phone_secondary,

        region=original.region,
        city=original.city,
        address=original.address,

        desired_position=original.desired_position,
        employment_type=original.employment_type,
        salary_expectation=original.salary_expectation,
        salary_currency=original.salary_currency,

        summary=original.summary,

        birth_date=original.birth_date,
        gender=original.gender,
        marital_status=original.marital_status,
        nationality=original.nationality,

        passport_series=original.passport_series,
        passport_number=original.passport_number,
        tin=original.tin,
        driver_license=original.driver_license,
        driver_license_category=original.driver_license_category,
        military_service=original.military_service,

        linkedin=original.linkedin,
        github=original.github,
        portfolio=original.portfolio,
    )


    for edu in original.educations.all():
        Education.objects.create(
            cv=new_cv,
            institution=edu.institution,
            degree=edu.degree,
            education_level=edu.education_level,
            field_of_study=edu.field_of_study,
            faculty=edu.faculty,
            start_year=edu.start_year,
            graduation_year=edu.graduation_year,
            gpa=edu.gpa,
            honors=edu.honors,
            diploma_number=edu.diploma_number,
            description=edu.description,
        )


    for exp in original.experiences.all():
        Experience.objects.create(
            cv=new_cv,
            company=exp.company,
            position=exp.position,
            employment_type=exp.employment_type,
            start_date=exp.start_date,
            end_date=exp.end_date,
            is_current=exp.is_current,
            company_location=exp.company_location,
            description=exp.description,
            technologies=exp.technologies,
            achievements=exp.achievements,
        )


    for s in original.skills.all():
        Skill.objects.create(
            cv=new_cv,
            name=s.name,
            category=s.category,
            level=s.level,
            years_of_experience=s.years_of_experience,
            description=s.description,
            last_used=s.last_used,
        )


    for lng in original.languages.all():
        Language.objects.create(
            cv=new_cv,
            name=lng.name,
            level=lng.level,
            certificate_type=lng.certificate_type,
            certificate_score=lng.certificate_score,
            is_native=lng.is_native,
        )


    for pr in original.projects.all():
        Project.objects.create(
            cv=new_cv,
            name=pr.name,
            role=pr.role,
            description=pr.description,
            technologies=pr.technologies,
            start_date=pr.start_date,
            end_date=pr.end_date,
            project_url=pr.project_url,
            is_personal=pr.is_personal,
        )


    for c in original.certificates.all():
        Certificate.objects.create(
            cv=new_cv,
            name=c.name,
            issuing_organization=c.issuing_organization,
            issue_date=c.issue_date,
            expiration_date=c.expiration_date,
            certificate_id=c.certificate_id,
            certificate_url=c.certificate_url,
            description=c.description,
            certificate_file=c.certificate_file,
        )

    messages.success(request, _("Rezyume muvaffaqiyatli nusxalandi!"))
    return redirect("cvbuilder:cv_list")


@login_required
def cv_delete(request, pk):
    profile = get_student_profile(request.user)
    if not profile:
        messages.error(request, _("You don't have StudentProfile."))
        return redirect("cvbuilder:cv_list")

    cv = get_object_or_404(CV, pk=pk, user=profile)

    if request.method == "POST":
        title = cv.title
        cv.delete()
        messages.success(request, _('"{title}" rezyumesi o\'chirildi').format(title=title))
        return redirect("cvbuilder:cv_list")

    return render(request, "cvbuilder/cv_confirm_delete.html", {"cv": cv})






@login_required
def update_cv_status(request, pk):
    profile = get_student_profile(request.user)
    if not profile:
        messages.error(request, _("You don't have StudentProfile."))
        return redirect("cvbuilder:cv_list")

    cv = get_object_or_404(CV, pk=pk, user=profile)

    if request.method == "POST":
        new_status = request.POST.get("status")
        if new_status in dict(CV.STATUS_CHOICES):
            cv.status = new_status
            if new_status == "published" and not cv.published_date:
                cv.published_date = timezone.now()
            cv.save()
            messages.success(
                request,
                _('Rezyume holati "{status}" ga o\'zgartirildi').format(status=cv.get_status_display()),
            )
        else:
            messages.error(request, _("Noto'g'ri holat"))

    return redirect("cvbuilder:cv_edit", pk=cv.pk)






@login_required
def public_cv_list(request):
    if not can_access_public_list(request.user):
        messages.error(request, _("Sizda ushbu sahifaga kirish huquqi yo'q."))
        return redirect("cvbuilder:cv_list")

    cvs = (
        CV.objects.filter(status="published")
        .select_related("template", "user")
        .prefetch_related("skills", "experiences", "educations", "languages", "projects", "certificates")
        .order_by("-created_at")
    )

    q = request.GET.get("q", "").strip()
    template_id = request.GET.get("template")
    region = request.GET.get("region", "").strip()
    city = request.GET.get("city", "").strip()
    sort = request.GET.get("sort", "newest")

    if q:
        cvs = cvs.filter(
            Q(full_name__icontains=q)
            | Q(title__icontains=q)
            | Q(summary__icontains=q)
            | Q(desired_position__icontains=q)
        )

    if template_id:
        try:
            template_id_int = int(template_id)
            cvs = cvs.filter(template_id=template_id_int)
        except (ValueError, TypeError):
            template_id_int = None
    else:
        template_id_int = None

    if region:
        cvs = cvs.filter(region__icontains=region)

    if city:
        cvs = cvs.filter(city__icontains=city)

    sort_mapping = {
        "newest": "-created_at",
        "oldest": "created_at",
        "name_asc": "full_name",
        "name_desc": "-full_name",
    }
    cvs = cvs.order_by(sort_mapping.get(sort, "-created_at"))

    paginator = Paginator(cvs, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    templates = CVTemplate.objects.filter(is_active=True).only("id", "name")
    regions = (
        CV.objects.filter(status="published")
        .exclude(region__isnull=True)
        .exclude(region="")
        .order_by("region")
        .values_list("region", flat=True)
        .distinct()
    )
    cities = (
        CV.objects.filter(status="published")
        .exclude(city__isnull=True)
        .exclude(city="")
        .order_by("city")
        .values_list("city", flat=True)
        .distinct()
    )

    context = {
        "page_obj": page_obj,
        "cvs": page_obj.object_list,
        "templates": templates,
        "regions": regions,
        "cities": cities,
        "q": q,
        "region_filter": region,
        "city_filter": city,
        "selected_template": template_id_int,
        "sort": sort,
        "user_type": getattr(request.user, "user_type", None),
        "can_export_published_cvs": (
            request.user.is_employer
            or user_has_admin_permission(request.user, "can_manage_resumes")
        ),
    }
    return render(request, "cvbuilder/public_cv_list.html", context)






@login_required
def cv_stats(request):
    profile = get_student_profile(request.user)
    if not profile:
        messages.error(request, _("You don't have StudentProfile."))
        return redirect("cvbuilder:cv_list")

    cvs = CV.objects.filter(user=profile)

    total_cvs = cvs.count()
    published_cvs = cvs.filter(status="published").count()
    draft_cvs = cvs.filter(status="draft").count()
    archived_cvs = cvs.filter(status="archived").count()

    published_percent = (published_cvs / total_cvs * 100) if total_cvs > 0 else 0
    draft_percent = (draft_cvs / total_cvs * 100) if total_cvs > 0 else 0
    archived_percent = (archived_cvs / total_cvs * 100) if total_cvs > 0 else 0

    stats = {
        "total_cvs": total_cvs,
        "published_cvs": published_cvs,
        "draft_cvs": draft_cvs,
        "archived_cvs": archived_cvs,
        "total_experience": sum(cv.experiences.count() for cv in cvs),
        "total_skills": sum(cv.skills.count() for cv in cvs),
        "total_education": sum(cv.educations.count() for cv in cvs),
        "total_languages": sum(cv.languages.count() for cv in cvs),
        "published_percent": published_percent,
        "draft_percent": draft_percent,
        "archived_percent": archived_percent,
    }

    return render(request, "cvbuilder/cv_stats.html", {"stats": stats})






@login_required
def add_education(request, pk):
    profile = get_student_profile(request.user)
    if not profile:
        return JsonResponse({"success": False, "error": "No StudentProfile"}, status=403)

    cv = get_object_or_404(CV, pk=pk, user=profile)

    if request.method == "POST":
        form = EducationForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.cv = cv
            obj.save()
            return JsonResponse({"success": True, "id": obj.id})
        return JsonResponse({"success": False, "errors": form.errors}, status=400)

    return JsonResponse({"success": False, "error": "Invalid request"}, status=405)


@login_required
def add_experience(request, pk):
    profile = get_student_profile(request.user)
    if not profile:
        return JsonResponse({"success": False, "error": "No StudentProfile"}, status=403)

    cv = get_object_or_404(CV, pk=pk, user=profile)

    if request.method == "POST":
        form = ExperienceForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.cv = cv
            obj.save()
            return JsonResponse({"success": True, "id": obj.id})
        return JsonResponse({"success": False, "errors": form.errors}, status=400)

    return JsonResponse({"success": False, "error": "Invalid request"}, status=405)


@login_required
def add_skill(request, pk):
    profile = get_student_profile(request.user)
    if not profile:
        return JsonResponse({"success": False, "error": "No StudentProfile"}, status=403)

    cv = get_object_or_404(CV, pk=pk, user=profile)

    if request.method == "POST":
        form = SkillForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.cv = cv
            obj.save()
            return JsonResponse({"success": True, "id": obj.id})
        return JsonResponse({"success": False, "errors": form.errors}, status=400)

    return JsonResponse({"success": False, "error": "Invalid request"}, status=405)


@login_required
def add_language(request, pk):
    profile = get_student_profile(request.user)
    if not profile:
        return JsonResponse({"success": False, "error": "No StudentProfile"}, status=403)

    cv = get_object_or_404(CV, pk=pk, user=profile)

    if request.method == "POST":
        form = LanguageForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.cv = cv
            obj.save()
            return JsonResponse({"success": True, "id": obj.id})
        return JsonResponse({"success": False, "errors": form.errors}, status=400)

    return JsonResponse({"success": False, "error": "Invalid request"}, status=405)


@login_required
def delete_education(request, pk):
    profile = get_student_profile(request.user)
    if not profile:
        return JsonResponse({"success": False, "error": "No StudentProfile"}, status=403)

    education = get_object_or_404(Education, pk=pk, cv__user=profile)
    education.delete()
    return JsonResponse({"success": True})


@login_required
def delete_experience(request, pk):
    profile = get_student_profile(request.user)
    if not profile:
        return JsonResponse({"success": False, "error": "No StudentProfile"}, status=403)

    experience = get_object_or_404(Experience, pk=pk, cv__user=profile)
    experience.delete()
    return JsonResponse({"success": True})


@login_required
def delete_skill(request, pk):
    profile = get_student_profile(request.user)
    if not profile:
        return JsonResponse({"success": False, "error": "No StudentProfile"}, status=403)

    skill = get_object_or_404(Skill, pk=pk, cv__user=profile)
    skill.delete()
    return JsonResponse({"success": True})


@login_required
def delete_language(request, pk):
    profile = get_student_profile(request.user)
    if not profile:
        return JsonResponse({"success": False, "error": "No StudentProfile"}, status=403)

    language = get_object_or_404(Language, pk=pk, cv__user=profile)
    language.delete()
    return JsonResponse({"success": True})




@login_required
def template_preview(request, template_id):
    template = get_object_or_404(CVTemplate, pk=template_id, is_active=True)


    profile = get_student_profile(request.user)
    if not profile:
        messages.error(request, _("Only users with StudentProfile can preview templates."))
        return redirect("cvbuilder:template_selector")


    cv = (
        CV.objects.filter(user=profile)
        .select_related("template", "user")
        .prefetch_related("skills", "experiences", "educations", "languages", "projects", "certificates")
        .filter(status="published")
        .first()
    ) or (
        CV.objects.filter(user=profile)
        .select_related("template", "user")
        .prefetch_related("skills", "experiences", "educations", "languages", "projects", "certificates")
        .first()
    )


    template_type = template.template_type or DEFAULT_TEMPLATE_TYPE
    template_path = f"{TEMPLATE_DIR}/{template_type}.html"

    return render(
        request,
        "cvbuilder/template_preview.html",
        {
            "template": template,
            "cv": cv,
            "template_path": template_path,
            "hide_chrome": True,
        },
    )
