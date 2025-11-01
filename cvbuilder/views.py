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
from .models import *
from .forms import *

class CVListView(ListView):
    """Список резюме пользователя"""
    model = CV
    template_name = 'cvbuilder/cv_list.html'
    context_object_name = 'cvs'
    
    def get_queryset(self):
        return CV.objects.filter(user=self.request.user)

@login_required
def cv_create(request):
    """Создание нового резюме"""
    if request.method == 'POST':
        form = CVForm(request.POST)
        if form.is_valid():
            cv = form.save(commit=False)
            cv.user = request.user
            cv.save()
            messages.success(request, _('Rezyume muvaffaqiyatli yaratildi!'))
            return redirect('cvbuilder:cv_edit', pk=cv.pk)
        else:
            messages.error(request, _('Rezyumeni to`lidiring!'))
    else:
        form = CVForm()
    
    templates = CVTemplate.objects.filter(is_active=True)
    
    return render(request, 'cvbuilder/cv_create.html', {
        'form': form,
        'templates': templates,
    })

@login_required
def cv_edit(request, pk):
    """Редактирование резюме"""
    cv = get_object_or_404(CV, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = CVForm(request.POST, instance=cv)
        if form.is_valid():
            form.save()
            messages.success(request, _('Rezyume yangilandi!'))
            return redirect('cvbuilder:cv_edit', pk=cv.pk)
    else:
        form = CVForm(instance=cv)
    
    # Формы для связанных моделей
    education_form = EducationForm()
    experience_form = ExperienceForm()
    skill_form = SkillForm()
    language_form = LanguageForm()
    
    context = {
        'cv': cv,
        'form': form,
        'education_form': education_form,
        'experience_form': experience_form,
        'skill_form': skill_form,
        'language_form': language_form,
    }
    return render(request, 'cvbuilder/cv_edit.html', context)

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
    
    template_path = f'cvbuilder/templates/{cv.template.template_file}'
    return render(request, template_path, {'cv': cv})

@login_required
def cv_export_pdf(request, pk):
    """Экспорт резюме в PDF"""
    cv = get_object_or_404(CV, pk=pk, user=request.user)
    
    try:
        # Рендерим HTML
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
        salary_expectation=original_cv.salary_expectation,
        summary=original_cv.summary,
    )
    
    # Копируем связанные объекты
    for education in original_cv.educations.all():
        Education.objects.create(
            cv=new_cv,
            institution=education.institution,
            degree=education.degree,
            field_of_study=education.field_of_study,
            graduation_year=education.graduation_year,
        )
    
    for experience in original_cv.experiences.all():
        Experience.objects.create(
            cv=new_cv,
            company=experience.company,
            position=experience.position,
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
        )
    
    # Копируем языки
    for language in original_cv.languages.all():
        Language.objects.create(
            cv=new_cv,
            name=language.name,
            level=language.level,
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
def add_language(request, pk):
    """Добавление языка через AJAX"""
    cv = get_object_or_404(CV, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = LanguageForm(request.POST)
        if form.is_valid():
            language = form.save(commit=False)
            language.cv = cv
            language.save()
            return JsonResponse({'success': True, 'id': language.id})
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
def delete_language(request, pk):
    """Удаление языка"""
    language = get_object_or_404(Language, pk=pk, cv__user=request.user)
    language.delete()
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
        'total_experience': sum(cv.experiences.count() for cv in cvs),
        'total_skills': sum(cv.skills.count() for cv in cvs),
        'total_education': sum(cv.educations.count() for cv in cvs),
        'total_languages': sum(cv.languages.count() for cv in cvs),
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