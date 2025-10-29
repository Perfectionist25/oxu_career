from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import TemplateView, DetailView, UpdateView, ListView
from django.utils.translation import gettext_lazy as _
from django.http import JsonResponse
from django.urls import reverse_lazy

User = get_user_model()

from .models import UserSkill, Skill, UserActivity, Notification
from .forms import UserRegistrationForm, UserUpdateForm, ProfileForm, SkillForm


# Authentication Views
class RegisterView(TemplateView):
    """User registration view"""
    template_name = 'accounts/register.html'
    
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('accounts:dashboard')
        form = UserRegistrationForm()
        return render(request, self.template_name, {'form': form})
    
    def post(self, request, *args, **kwargs):
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, _('Muvaffaqiyatli ro\'yxatdan o\'tdingiz!'))
            return redirect('accounts:dashboard')
        return render(request, self.template_name, {'form': form})


def login_view(request):
    """User login view"""
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            
            # Create login activity
            UserActivity.objects.create(
                user=user,
                activity_type='login',
                description=_('User logged in'),
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:200]
            )
            
            messages.success(request, _('Xush kelibsiz!'))
            next_url = request.GET.get('next', 'accounts:dashboard')
            return redirect(next_url)
        else:
            messages.error(request, _('Login yoki parol noto\'g\'ri'))
    
    return render(request, 'accounts/login.html')


@login_required
def logout_view(request):
    """User logout view"""
    logout(request)
    messages.info(request, _('Tizimdan chiqdingiz'))
    return redirect('core:home')


# Profile Views
class DashboardView(LoginRequiredMixin, TemplateView):
    """User dashboard view"""
    template_name = 'accounts/dashboard.html'
    login_url = '/accounts/login/'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        context.update({
            'user': user,
            'recent_activities': UserActivity.objects.filter(user=user)[:10],
            'unread_notifications': Notification.objects.filter(user=user, is_read=False)[:5],
            'user_skills': UserSkill.objects.filter(user=user).select_related('skill'),
        })
        
        return context


class ProfileDetailView(LoginRequiredMixin, DetailView):
    """User profile detail view"""
    model = User
    template_name = 'accounts/profile.html'
    context_object_name = 'profile_user'
    
    def get_object(self):
        pk = self.kwargs.get('pk')
        if pk:
            return get_object_or_404(User, pk=pk)
        return self.request.user


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """User profile update view"""
    model = User
    form_class = ProfileForm
    template_name = 'accounts/profile_edit.html'
    success_url = reverse_lazy('accounts:profile')
    
    def get_object(self):
        return self.request.user
    
    def form_valid(self, form):
        messages.success(self.request, _('Profil muvaffaqiyatli yangilandi!'))
        
        # Create activity
        UserActivity.objects.create(
            user=self.request.user,
            activity_type='profile_update',
            description=_('Profile updated')
        )
        
        return super().form_valid(form)


# Notification Views
@login_required
def notification_list(request):
    """List all notifications"""
    notifications = Notification.objects.filter(user=request.user)
    return render(request, 'accounts/notifications.html', {
        'notifications': notifications
    })


@login_required
def mark_notification_read(request, pk):
    """Mark notification as read"""
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.mark_as_read()
    return redirect('accounts:notifications')


# Activity Views
@login_required
def activity_log(request):
    """View user activity log"""
    activities = UserActivity.objects.filter(user=request.user)
    return render(request, 'accounts/activity_log.html', {
        'activities': activities
    })


# Skill Views
@login_required
def skill_list(request):
    """List user skills"""
    user_skills = UserSkill.objects.filter(user=request.user).select_related('skill')
    return render(request, 'accounts/skills.html', {
        'user_skills': user_skills
    })


@login_required
def add_skill(request):
    """Add a new skill"""
    if request.method == 'POST':
        form = SkillForm(request.POST)
        if form.is_valid():
            user_skill = form.save(commit=False)
            user_skill.user = request.user
            user_skill.save()
            messages.success(request, _('Ko\'nikma qo\'shildi!'))
            return redirect('accounts:skill_list')
    else:
        form = SkillForm()
    
    return render(request, 'accounts/add_skill.html', {'form': form})


@login_required
def remove_skill(request, pk):
    """Remove a skill"""
    user_skill = get_object_or_404(UserSkill, pk=pk, user=request.user)
    user_skill.delete()
    messages.success(request, _('Ko\'nikma o\'chirildi!'))
    return redirect('accounts:skill_list')


# AJAX Views
@login_required
def update_notification_settings(request):
    """Update notification settings via AJAX"""
    if request.method == 'POST':
        user = request.user
        user.email_notifications = request.POST.get('email_notifications') == 'true'
        user.job_alerts = request.POST.get('job_alerts') == 'true'
        user.newsletter = request.POST.get('newsletter') == 'true'
        user.save()
        
        return JsonResponse({'success': True, 'message': _('Sozlamalar saqlandi')})
    
    return JsonResponse({'success': False, 'message': _('Xato yuz berdi')})


@login_required
def get_unread_notification_count(request):
    """Get unread notification count via AJAX"""
    count = Notification.objects.filter(user=request.user, is_read=False).count()
    return JsonResponse({'count': count})
