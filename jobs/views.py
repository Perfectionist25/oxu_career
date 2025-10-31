from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count, Avg
from django.views.generic import ListView, DetailView
from django.utils import timezone
from .models import *
from django.views.decorators.http import require_POST
from .forms import (
    JobSearchForm, JobApplicationForm, JobAlertForm, CompanyReviewForm,
    InterviewExperienceForm, ApplicationStatusForm
)

@login_required
def employer_applications(request):
    """View for employers to see all applications to their jobs"""
    if not request.user.is_employer:
        messages.error(request, _("Only employers can access this page."))
        return redirect('jobs:list')
    
    # Get all companies owned by this user
    user_companies = Company.objects.filter(owner=request.user)
    
    if not user_companies.exists():
        messages.info(request, _("You need to create a company first to view applications."))
        return redirect('jobs:company_create')  # You might need to adjust this URL
    
    # Get all jobs from user's companies
    employer_jobs = Job.objects.filter(company__in=user_companies)
    
    # Get applications with related data
    applications = JobApplication.objects.filter(
        job__in=employer_jobs
    ).select_related(
        'job', 'job__company', 'candidate', 'cv'
    ).order_by('-created_at')
    
    # Filter by status if provided
    status_filter = request.GET.get('status')
    if status_filter:
        applications = applications.filter(status=status_filter)
    
    # Count applications by status
    status_counts = {
        'total': applications.count(),
        'applied': applications.filter(status='applied').count(),
        'reviewed': applications.filter(status='reviewed').count(),
        'shortlisted': applications.filter(status='shortlisted').count(),
        'interview': applications.filter(status='interview').count(),
        'rejected': applications.filter(status='rejected').count(),
        'hired': applications.filter(status='hired').count(),
    }
    
    context = {
        'applications': applications,
        'status_filter': status_filter,
        'status_counts': status_counts,
        'user_companies': user_companies,
    }
    
    return render(request, 'jobs/employer_applications.html', context)

@login_required
def job_create(request):
    """Create a new job posting"""
    # Check if user is an employer
    if not request.user.is_employer:
        messages.error(request, _("Only employers can create job postings."))
        return redirect('jobs:list')
    
    # Get companies that the user can post jobs for
    user_companies = Company.objects.filter(owner=request.user, is_active=True)
    
    if not user_companies.exists():
        messages.error(request, _("You need to create a company first before posting jobs."))
        return redirect('companies:create')  # You might need to create this URL
    
    if request.method == 'POST':
        form = JobForm(request.POST, user=request.user)
        if form.is_valid():
            job = form.save(commit=False)
            job.created_by = request.user
            job.save()
            
            # Handle save as draft or publish
            if 'save_draft' in request.POST:
                job.is_active = False
                job.save()
                messages.success(request, _("Job saved as draft successfully."))
            else:  # publish
                job.is_active = True
                job.save()
                messages.success(request, _("Job published successfully!"))
            
            return redirect('jobs:my_jobs')
    else:
        form = JobForm(user=request.user)
    
    context = {
        'form': form,
        'user_companies': user_companies,
        'today': timezone.now().date(),
    }
    
    return render(request, 'jobs/job_form.html', context)

@login_required
def my_jobs(request):
    """Мои вакансии (для работодателей) и мои заявки (для студентов)"""
    context = {}
    
    if hasattr(request.user, 'is_employer') and request.user.is_employer:
        # Для работодателя - показываем созданные вакансии
        jobs = Job.objects.filter(company__contact_email=request.user.email).order_by('-created_at')
        
        # Статистика
        total_jobs = jobs.count()
        active_jobs = jobs.filter(is_active=True).count()
        draft_jobs = jobs.filter(is_active=False).count()
        
        # Пагинация
        paginator = Paginator(jobs, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context.update({
            'jobs': page_obj,
            'total_jobs': total_jobs,
            'active_jobs': active_jobs,
            'draft_jobs': draft_jobs,
            'is_employer_view': True,
        })
        
    elif hasattr(request.user, 'is_student') and request.user.is_student:
        # Для студента - показываем заявки на вакансии
        applications = JobApplication.objects.filter(candidate=request.user).select_related('job', 'job__company').order_by('-created_at')
        
        # Статистика
        total_applications = applications.count()
        pending_applications = applications.filter(status='applied').count()
        reviewed_applications = applications.filter(status='reviewed').count()
        interview_applications = applications.filter(status='interview').count()
        accepted_applications = applications.filter(status='hired').count()
        rejected_applications = applications.filter(status='rejected').count()
        
        # Пагинация
        paginator = Paginator(applications, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context.update({
            'applications': page_obj,
            'total_applications': total_applications,
            'pending_applications': pending_applications,
            'reviewed_applications': reviewed_applications,
            'interview_applications': interview_applications,
            'accepted_applications': accepted_applications,
            'rejected_applications': rejected_applications,
            'is_student_view': True,
        })
    
    else:
        messages.error(request, _("Sizda bu sahifani ko'rish huquqi yo'q"))
        return redirect('accounts:home')
    
    return render(request, 'jobs/my_jobs.html', context)

@login_required
def saved_jobs(request):
    """Сохраненные вакансии"""
    if not hasattr(request.user, 'is_student') or not request.user.is_student:
        messages.error(request, _("Sizda bu sahifani ko'rish huquqi yo'q"))
        return redirect('accounts:home')
    
    saved_jobs = SavedJob.objects.filter(user=request.user).select_related('job', 'job__company').order_by('-created_at')
    
    # Пагинация
    paginator = Paginator(saved_jobs, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'saved_jobs': page_obj,
        'total_saved': saved_jobs.count(),
    }
    
    return render(request, 'jobs/saved_jobs.html', context)


def job_list(request):
    """Список вакансий"""
    form = JobSearchForm(request.GET or None)
    jobs = Job.objects.filter(is_active=True)
    
    if form.is_valid():
        query = form.cleaned_data.get('query')
        location = form.cleaned_data.get('location')
        industry = form.cleaned_data.get('industry')
        employment_type = form.cleaned_data.get('employment_type')
        experience_level = form.cleaned_data.get('experience_level')
        education_level = form.cleaned_data.get('education_level')
        remote_work = form.cleaned_data.get('remote_work')
        salary_min = form.cleaned_data.get('salary_min')
        
        if query:
            jobs = jobs.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(company__name__icontains=query) |
                Q(skills_required__icontains=query)
            )
        
        if location:
            jobs = jobs.filter(location__icontains=location)
        
        if industry:
            jobs = jobs.filter(company__industry=industry)
        
        if employment_type:
            jobs = jobs.filter(employment_type__in=employment_type)
        
        if experience_level:
            jobs = jobs.filter(experience_level__in=experience_level)
        
        if education_level:
            jobs = jobs.filter(education_level__in=education_level)
        
        if remote_work:
            jobs = jobs.filter(remote_work=True)
        
        if salary_min:
            jobs = jobs.filter(
                Q(salary_min__gte=salary_min) |
                Q(salary_max__gte=salary_min) |
                Q(salary_negotiable=True)
            )
    
    # Сортировка
    sort = request.GET.get('sort', 'newest')
    if sort == 'relevance':
        jobs = jobs.order_by('-is_featured', '-is_urgent', '-created_at')
    elif sort == 'salary':
        jobs = jobs.order_by('-salary_max', '-salary_min')
    else:  # newest
        jobs = jobs.order_by('-created_at')
    
    # Пагинация
    paginator = Paginator(jobs, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Статистика
    total_jobs = jobs.count()
    featured_jobs = jobs.filter(is_featured=True)[:5]
    
    context = {
        'page_obj': page_obj,
        'form': form,
        'total_jobs': total_jobs,
        'featured_jobs': featured_jobs,
        'industries': Industry.objects.annotate(job_count=Count('company__jobs')),
    }
    return render(request, 'jobs/job_list.html', context)

def job_detail(request, pk):
    """Детальная страница вакансии"""
    job = get_object_or_404(Job, pk=pk, is_active=True)
    
    # Увеличиваем счетчик просмотров
    job.views_count += 1
    job.save()
    
    # Проверяем, откликался ли пользователь
    has_applied = False
    application = None
    if request.user.is_authenticated:
        try:
            application = JobApplication.objects.get(job=job, candidate=request.user)
            has_applied = True
        except JobApplication.DoesNotExist:
            pass
    
    # Проверяем, сохранена ли вакансия
    is_saved = False
    if request.user.is_authenticated:
        is_saved = SavedJob.objects.filter(job=job, user=request.user).exists()
    
    # Форма для отклика
    application_form = JobApplicationForm()
    
    # Похожие вакансии
    similar_jobs = Job.objects.filter(
        is_active=True,
        company__industry=job.company.industry,
        experience_level=job.experience_level
    ).exclude(pk=job.pk)[:4]
    
    context = {
        'job': job,
        'has_applied': has_applied,
        'application': application,
        'is_saved': is_saved,
        'application_form': application_form,
        'similar_jobs': similar_jobs,
    }
    return render(request, 'jobs/job_detail.html', context)

@require_POST
def increment_job_views(request, pk):
    job = get_object_or_404(Job, pk=pk)
    job.views_count += 1
    job.save()
    return JsonResponse({'success': True, 'views_count': job.views_count})

@login_required
def apply_for_job(request, pk):
    """Отклик на вакансию"""
    job = get_object_or_404(Job, pk=pk, is_active=True)
    
    # Проверяем, не откликался ли уже
    if JobApplication.objects.filter(job=job, candidate=request.user).exists():
        messages.warning(request, _('You have already applied for this job.'))
        return redirect('jobs:job_detail', pk=job.pk)
    
    # Проверяем, не истекла ли вакансия
    if job.is_expired():
        messages.error(request, _('This job posting has expired.'))
        return redirect('jobs:job_detail', pk=job.pk)
    
    if request.method == 'POST':
        form = JobApplicationForm(request.POST)
        if form.is_valid():
            application = form.save(commit=False)
            application.job = job
            application.candidate = request.user
            application.save()
            
            # Увеличиваем счетчик откликов
            job.applications_count += 1
            job.save()
            
            messages.success(request, _('Your application has been submitted successfully!'))
            return redirect('jobs:job_detail', pk=job.pk)
    else:
        form = JobApplicationForm()
    
    context = {
        'job': job,
        'form': form,
    }
    return render(request, 'jobs/apply_for_job.html', context)

@login_required
def save_job(request, pk):
    """Сохранение вакансии"""
    job = get_object_or_404(Job, pk=pk, is_active=True)
    
    if request.method == 'POST':
        saved_job, created = SavedJob.objects.get_or_create(
            job=job,
            user=request.user
        )
        
        if created:
            messages.success(request, _('Job saved successfully!'))
        else:
            messages.info(request, _('Job is already saved.'))
    
    return redirect('jobs:job_detail', pk=job.pk)

@login_required
def unsave_job(request, pk):
    """Удаление вакансии из сохраненных"""
    job = get_object_or_404(Job, pk=pk)
    
    if request.method == 'POST':
        SavedJob.objects.filter(job=job, user=request.user).delete()
        messages.success(request, _('Job removed from saved list.'))
    
    return redirect('jobs:job_detail', pk=job.pk)

@login_required
def saved_jobs(request):
    """Сохраненные вакансии"""
    saved_jobs = SavedJob.objects.filter(user=request.user).select_related('job', 'job__company')
    
    context = {
        'saved_jobs': saved_jobs,
    }
    return render(request, 'jobs/saved_jobs.html', context)

@login_required
def my_applications(request):
    """Мои отклики"""
    applications = JobApplication.objects.filter(
        candidate=request.user
    ).select_related('job', 'job__company').order_by('-created_at')
    
    # Статистика
    stats = applications.aggregate(
        total=Count('id'),
        applied=Count('id', filter=Q(status='applied')),
        reviewed=Count('id', filter=Q(status='reviewed')),
        interview=Count('id', filter=Q(status='interview')),
        hired=Count('id', filter=Q(status='hired')),
    )
    
    context = {
        'applications': applications,
        'stats': stats,
    }
    return render(request, 'jobs/my_applications.html', context)

def company_list(request):
    """Список компаний"""
    companies = Company.objects.filter(is_active=True, is_verified=True)
    
    # Фильтрация
    industry_id = request.GET.get('industry')
    if industry_id:
        companies = companies.filter(industry_id=industry_id)
    
    query = request.GET.get('q')
    if query:
        companies = companies.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query)
        )
    
    # Пагинация
    paginator = Paginator(companies, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'industries': Industry.objects.all(),
        'total_companies': companies.count(),
    }
    return render(request, 'jobs/company_list.html', context)

def company_detail(request, pk):
    """Детальная страница компании"""
    company = get_object_or_404(Company, pk=pk, is_active=True)
    
    # Активные вакансии
    jobs = company.jobs.filter(is_active=True)
    
    # Отзывы
    reviews = company.reviews.filter(is_published=True)
    
    # Статистика отзывов
    review_stats = reviews.aggregate(
        avg_overall=Avg('overall_rating'),
        avg_work_life=Avg('work_life_balance'),
        avg_salary=Avg('salary_benefits'),
        avg_growth=Avg('career_growth'),
        avg_management=Avg('management'),
        total_reviews=Count('id')
    )
    
    # Опыт собеседований
    interview_experiences = company.interview_experiences.filter(is_published=True)[:5]
    
    context = {
        'company': company,
        'jobs': jobs,
        'reviews': reviews,
        'interview_experiences': interview_experiences,
        'review_stats': review_stats,
    }
    return render(request, 'jobs/company_detail.html', context)

@login_required
def create_company_review(request, pk):
    """Создание отзыва о компании"""
    company = get_object_or_404(Company, pk=pk, is_active=True)
    
    # Проверяем, не оставлял ли пользователь уже отзыв
    if CompanyReview.objects.filter(company=company, author=request.user).exists():
        messages.warning(request, _('You have already reviewed this company.'))
        return redirect('jobs:company_detail', pk=company.pk)
    
    if request.method == 'POST':
        form = CompanyReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.company = company
            review.author = request.user
            review.save()
            
            messages.success(request, _('Thank you for your review! It will be published after verification.'))
            return redirect('jobs:company_detail', pk=company.pk)
    else:
        form = CompanyReviewForm()
    
    context = {
        'company': company,
        'form': form,
    }
    return render(request, 'jobs/create_company_review.html', context)

@login_required
def create_interview_experience(request, pk):
    """Создание опыта собеседования"""
    company = get_object_or_404(Company, pk=pk, is_active=True)
    
    if request.method == 'POST':
        form = InterviewExperienceForm(request.POST)
        if form.is_valid():
            experience = form.save(commit=False)
            experience.company = company
            experience.author = request.user
            experience.save()
            
            messages.success(request, _('Thank you for sharing your interview experience!'))
            return redirect('jobs:company_detail', pk=company.pk)
    else:
        form = InterviewExperienceForm(initial={'company': company})
    
    context = {
        'company': company,
        'form': form,
    }
    return render(request, 'jobs/create_interview_experience.html', context)

@login_required
def job_alerts(request):
    """Управление оповещениями о вакансиях"""
    alerts = JobAlert.objects.filter(user=request.user)
    
    if request.method == 'POST':
        form = JobAlertForm(request.POST)
        if form.is_valid():
            alert = form.save(commit=False)
            alert.user = request.user
            alert.save()
            
            messages.success(request, _('Job alert created successfully!'))
            return redirect('jobs:job_alerts')
    else:
        form = JobAlertForm()
    
    context = {
        'alerts': alerts,
        'form': form,
    }
    return render(request, 'jobs/job_alerts.html', context)

@login_required
def delete_job_alert(request, pk):
    """Удаление оповещения о вакансиях"""
    alert = get_object_or_404(JobAlert, pk=pk, user=request.user)
    
    if request.method == 'POST':
        alert.delete()
        messages.success(request, _('Job alert deleted successfully!'))
    
    return redirect('jobs:job_alerts')

# AJAX views
@login_required
def update_application_status(request, pk):
    """Обновление статуса отклика (AJAX)"""
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        application = get_object_or_404(JobApplication, pk=pk, candidate=request.user)
        new_status = request.POST.get('status')
        
        if new_status in dict(JobApplication.STATUS_CHOICES):
            application.status = new_status
            application.save()
            
            return JsonResponse({
                'success': True,
                'new_status': application.get_status_display(),
                'status_class': new_status,
            })
    
    return JsonResponse({'success': False})

@login_required
def get_user_cvs(request):
    """Получение резюме пользователя (AJAX)"""
    from cvbuilder.models import CV
    cvs = CV.objects.filter(user=request.user, status='published')
    
    cv_list = [{
        'id': cv.id,
        'title': cv.title,
        'full_name': cv.full_name,
    } for cv in cvs]
    
    return JsonResponse({'cvs': cv_list})

class CompanyJobsView(DetailView):
    """Вакансии конкретной компании"""
    model = Company
    template_name = 'jobs/company_jobs.html'
    context_object_name = 'company'
    
    def get_queryset(self):
        return Company.objects.filter(is_active=True)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['jobs'] = self.object.jobs.filter(is_active=True)
        return context

def industries_list(request):
    """Список отраслей"""
    industries = Industry.objects.annotate(
        job_count=Count('company__jobs', filter=Q(company__jobs__is_active=True)),
        company_count=Count('company', filter=Q(company__is_active=True))
    ).order_by('name')
    
    context = {
        'industries': industries,
    }
    return render(request, 'jobs/industries_list.html', context)