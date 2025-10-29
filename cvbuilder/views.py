from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.generic import ListView
from django.urls import reverse_lazy
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _
import tempfile
import os
from .models import CV, Education, Experience, Skill, Project, Language, Certificate, CVTemplate
from .forms import (
    CVForm, EducationForm, ExperienceForm, SkillForm, 
    ProjectForm, LanguageForm, CertificateForm, CVSettingsForm
)

class CVListView(ListView):
    """Список резюме пользователя"""
    model = CV
    template_name = 'cvbuilder/cv_list.html'  # Исправлено имя шаблона
    context_object_name = 'cvs'
    
    def get_queryset(self):
        return CV.objects.filter(user=self.request.user)

@login_required
def cv_create(request):
    """Создание нового резюме"""
    if request.method == 'POST':
        form = CVForm(request.POST, request.FILES)
        if form.is_valid():
            cv = form.save(commit=False)
            cv.user = request.user
            cv.save()
            messages.success(request, _('Rezyume muvaffaqiyatli yaratildi!'))
            return redirect('cvbuilder:cv_edit', pk=cv.pk)  # Исправлено имя URL
    else:
        form = CVForm()
    
    templates = CVTemplate.objects.filter(is_active=True)
    
    return render(request, 'cvbuilder/cv_create.html', {  # Исправлено имя шаблона
        'form': form,
        'templates': templates,
    })

@login_required
def cv_edit(request, pk):
    """Редактирование резюме"""
    cv = get_object_or_404(CV, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = CVForm(request.POST, request.FILES, instance=cv)
        if form.is_valid():
            form.save()
            messages.success(request, _('Rezyume yangilandi!'))
            return redirect('cvbuilder:cv_edit', pk=cv.pk)  # Исправлено имя URL
    else:
        form = CVForm(instance=cv)
    
    # Формы для связанных моделей
    education_form = EducationForm()
    experience_form = ExperienceForm()
    skill_form = SkillForm()
    project_form = ProjectForm()
    language_form = LanguageForm()
    certificate_form = CertificateForm()
    
    context = {
        'cv': cv,
        'form': form,
        'education_form': education_form,
        'experience_form': experience_form,
        'skill_form': skill_form,
        'project_form': project_form,
        'language_form': language_form,
        'certificate_form': certificate_form,
    }
    return render(request, 'cvbuilder/cv_edit.html', context)  # Исправлено имя шаблона

@login_required
def cv_detail(request, pk):
    """Просмотр резюме"""
    cv = get_object_or_404(CV, pk=pk)
    
    # Проверяем доступ (только владелец или опубликованное резюме)
    if cv.user != request.user and cv.status != 'published':
        messages.error(request, _('Sizga ushbu rezyumega kirish huquqi yo\'q.'))
        return redirect('cvbuilder:cv_list')
    
    return render(request, 'cvbuilder/cv_detail.html', {'cv': cv})

@login_required
def cv_preview(request, pk):
    """Предпросмотр резюме"""
    cv = get_object_or_404(CV, pk=pk, user=request.user)
    
    # Исправлено: убрана лишняя папка templates из пути
    template_path = f'cvbuilder/templates/{cv.template.template_file}'
    return render(request, template_path, {'cv': cv})

@login_required
def cv_export_pdf(request, pk):
    """Экспорт резюме в PDF"""
    cv = get_object_or_404(CV, pk=pk, user=request.user)
    
    try:
        # Рендерим HTML (исправлен путь к шаблону)
        html_string = render_to_string(f'cvbuilder/templates/{cv.template.template_file}', {'cv': cv})
        
        # Создаем PDF (нужно установить weasyprint)
        from weasyprint import HTML
        html = HTML(string=html_string)
        pdf_file = html.write_pdf()
        
        response = HttpResponse(pdf_file, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{cv.title}.pdf"'
        
        return response
        
    except ImportError:
        messages.error(request, _('PDF eksport qilish imkoniyati hozircha mavjud emas.'))
        return redirect('cvbuilder:cv_detail', pk=cv.pk)
    except Exception as e:
        messages.error(request, _('PDF yaratishda xatolik yuz berdi.'))
        return redirect('cvbuilder:cv_detail', pk=cv.pk)

@login_required
def cv_duplicate(request, pk):
    """Дублирование резюме"""
    original_cv = get_object_or_404(CV, pk=pk, user=request.user)
    
    # Создаем копию основного объекта CV
    new_cv = CV.objects.create(
        user=request.user,
        title=f"{original_cv.title} (nusxa)",
        template=original_cv.template,
        status='draft',
        full_name=original_cv.full_name,
        email=original_cv.email,
        phone=original_cv.phone,
        location=original_cv.location,
        photo=original_cv.photo,
        summary=original_cv.summary,
        show_photo=original_cv.show_photo,
        show_email=original_cv.show_email,
        show_phone=original_cv.show_phone,
        linkedin=original_cv.linkedin,
        github=original_cv.github,
        portfolio=original_cv.portfolio,
    )
    
    # Копируем связанные объекты
    for education in original_cv.educations.all():
        Education.objects.create(
            cv=new_cv,
            institution=education.institution,
            degree=education.degree,
            field_of_study=education.field_of_study,
            start_date=education.start_date,
            end_date=education.end_date,
            is_current=education.is_current,
            description=education.description,
        )
    
    for experience in original_cv.experiences.all():
        Experience.objects.create(
            cv=new_cv,
            company=experience.company,
            position=experience.position,
            location=experience.location,
            start_date=experience.start_date,
            end_date=experience.end_date,
            is_current=experience.is_current,
            description=experience.description,
        )
    
    for skill in original_cv.skills.all():
        Skill.objects.create(
            cv=new_cv,
            name=skill.name,
            level=skill.level,
            category=skill.category,
            years_of_experience=skill.years_of_experience,
        )
    
    # Копируем проекты
    for project in original_cv.projects.all():
        Project.objects.create(
            cv=new_cv,
            name=project.name,
            description=project.description,
            technologies=project.technologies,
            url=project.url,
            start_date=project.start_date,
            end_date=project.end_date,
        )
    
    # Копируем языки
    for language in original_cv.languages.all():
        Language.objects.create(
            cv=new_cv,
            name=language.name,
            level=language.level,
        )
    
    # Копируем сертификаты
    for certificate in original_cv.certificates.all():
        Certificate.objects.create(
            cv=new_cv,
            name=certificate.name,
            organization=certificate.organization,
            issue_date=certificate.issue_date,
            expiry_date=certificate.expiry_date,
            credential_id=certificate.credential_id,
            url=certificate.url,
        )
    
    messages.success(request, _('Rezyume muvaffaqiyatli nusxalandi!'))
    return redirect('cvbuilder:cv_edit', pk=new_cv.pk)

# AJAX views для динамического добавления элементов
@login_required
def add_education(request, pk):
    """Добавление образования через AJAX"""
    cv = get_object_or_404(CV, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = EducationForm(request.POST)
        if form.is_valid():
            education = form.save(commit=False)
            education.cv = cv
            education.save()
            return JsonResponse({'success': True, 'id': education.id})
        else:
            return JsonResponse({'success': False, 'errors': form.errors})
    
    return JsonResponse({'success': False, 'error': _('Noto\'g\'ri so\'rov')})

@login_required
def add_experience(request, pk):
    """Добавление опыта работы через AJAX"""
    cv = get_object_or_404(CV, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = ExperienceForm(request.POST)
        if form.is_valid():
            experience = form.save(commit=False)
            experience.cv = cv
            experience.save()
            return JsonResponse({'success': True, 'id': experience.id})
        else:
            return JsonResponse({'success': False, 'errors': form.errors})
    
    return JsonResponse({'success': False, 'error': _('Noto\'g\'ri so\'rov')})

@login_required
def add_skill(request, pk):
    """Добавление навыка через AJAX"""
    cv = get_object_or_404(CV, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = SkillForm(request.POST)
        if form.is_valid():
            skill = form.save(commit=False)
            skill.cv = cv
            skill.save()
            return JsonResponse({'success': True, 'id': skill.id})
        else:
            return JsonResponse({'success': False, 'errors': form.errors})
    
    return JsonResponse({'success': False, 'error': _('Noto\'g\'ri so\'rov')})

@login_required
def delete_education(request, pk):
    """Удаление образования"""
    education = get_object_or_404(Education, pk=pk, cv__user=request.user)
    education.delete()
    return JsonResponse({'success': True})

@login_required
def delete_experience(request, pk):
    """Удаление опыта работы"""
    experience = get_object_or_404(Experience, pk=pk, cv__user=request.user)
    experience.delete()
    return JsonResponse({'success': True})

@login_required
def delete_skill(request, pk):
    """Удаление навыка"""
    skill = get_object_or_404(Skill, pk=pk, cv__user=request.user)
    skill.delete()
    return JsonResponse({'success': True})

@login_required
def update_cv_status(request, pk):
    """Обновление статуса резюме"""
    cv = get_object_or_404(CV, pk=pk, user=request.user)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(CV.STATUS_CHOICES):
            cv.status = new_status
            cv.save()
            messages.success(request, _('Rezyume holati "{status}" ga o\'zgartirildi').format(
                status=cv.get_status_display()
            ))
        else:
            messages.error(request, _('Noto\'g\'ri holat'))
    
    return redirect('cvbuilder:cv_edit', pk=cv.pk)

def template_preview(request, template_id):
    """Предпросмотр шаблона"""
    template = get_object_or_404(CVTemplate, pk=template_id)
    return render(request, 'cvbuilder/template_preview.html', {'template': template})

@login_required
def cv_stats(request):
    """Статистика по резюме пользователя"""
    cvs = CV.objects.filter(user=request.user)
    
    stats = {
        'total_cvs': cvs.count(),
        'published_cvs': cvs.filter(status='published').count(),
        'draft_cvs': cvs.filter(status='draft').count(),
        'archived_cvs': cvs.filter(status='archived').count(),
        'total_experience': sum(cv.experiences.count() for cv in cvs),
        'total_skills': sum(cv.skills.count() for cv in cvs),
        'total_education': sum(cv.educations.count() for cv in cvs),
        'total_projects': sum(cv.projects.count() for cv in cvs),
        'total_languages': sum(cv.languages.count() for cv in cvs),
        'total_certificates': sum(cv.certificates.count() for cv in cvs),
    }
    
    return render(request, 'cvbuilder/cv_stats.html', {'stats': stats})

@login_required
def cv_delete(request, pk):
    """Удаление резюме"""
    cv = get_object_or_404(CV, pk=pk, user=request.user)
    
    if request.method == 'POST':
        cv_title = cv.title
        cv.delete()
        messages.success(request, _('"{title}" rezyumesi o\'chirildi').format(title=cv_title))
        return redirect('cvbuilder:cv_list')
    
    return render(request, 'cvbuilder/cv_confirm_delete.html', {'cv': cv})