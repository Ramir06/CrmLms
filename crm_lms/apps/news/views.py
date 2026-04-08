from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.db import models

from apps.core.mixins import admin_required, mentor_required
from .models import News
from .forms import NewsForm


def admin_or_mentor_required(view_func):
    """Декоратор разрешающий доступ админам и менторам"""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(request.get_full_path())
        
        if request.user.role in ('admin', 'superadmin', 'mentor'):
            return view_func(request, *args, **kwargs)
        
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied("У вас нет прав доступа к этой странице")
    
    return wrapper


@login_required
@admin_or_mentor_required
def news_list_admin(request):
    news = News.objects.select_related('created_by').all()
    return render(request, 'admin/news/list.html', {'news': news, 'page_title': 'Объявления'})


@login_required
@admin_required
def news_create(request):
    form = NewsForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        obj = form.save(commit=False)
        obj.created_by = request.user
        if obj.is_published and not obj.published_at:
            obj.published_at = timezone.now()
        obj.save()
        messages.success(request, 'Новость создана.')
        return redirect('news:admin_list')
    return render(request, 'admin/news/form.html', {'form': form, 'page_title': 'Создать новость'})


@login_required
@admin_required
def news_edit(request, pk):
    obj = get_object_or_404(News, pk=pk)
    form = NewsForm(request.POST or None, request.FILES or None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        news = form.save(commit=False)
        if news.is_published and not news.published_at:
            news.published_at = timezone.now()
        news.save()
        messages.success(request, 'Новость обновлена.')
        return redirect('news:admin_list')
    return render(request, 'admin/news/form.html', {'form': form, 'news': obj, 'page_title': 'Редактировать новость'})


@login_required
@admin_required
def news_delete(request, pk):
    obj = get_object_or_404(News, pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Новость удалена.')
    return redirect('news:admin_list')


@login_required
@admin_required
def news_toggle_publish(request, pk):
    obj = get_object_or_404(News, pk=pk)
    obj.is_published = not obj.is_published
    if obj.is_published and not obj.published_at:
        obj.published_at = timezone.now()
    obj.save()
    return redirect('news:admin_list')


@login_required
def news_list_student(request):
    """Список новостей для студентов"""
    user = request.user
    
    # Фильтруем по организации студента
    organization = None
    if hasattr(user, 'student_profile') and user.student_profile.organization:
        organization = user.student_profile.organization
    
    # Получаем новости для студентов
    news_query = News.objects.filter(is_published=True)
    
    if organization:
        news_query = news_query.filter(
            models.Q(organization=organization) | models.Q(organization__isnull=True)
        )
    
    # Фильтруем по аудитории
    news_query = news_query.filter(
        models.Q(audience__in=['all', 'students'])
    )
    
    news = news_query.select_related('created_by').order_by('-published_at')
    
    return render(request, 'students/news/list.html', {
        'news': news, 
        'page_title': 'Объявления'
    })


@login_required
def news_detail_student(request, pk):
    """Детальная новость для студентов"""
    user = request.user
    
    # Фильтруем по организации студента
    organization = None
    if hasattr(user, 'student_profile') and user.student_profile.organization:
        organization = user.student_profile.organization
    
    # Получаем новость
    news_query = News.objects.filter(is_published=True, pk=pk)
    
    if organization:
        news_query = news_query.filter(
            models.Q(organization=organization) | models.Q(organization__isnull=True)
        )
    
    news = get_object_or_404(news_query, audience__in=['all', 'students'])
    
    return render(request, 'students/news/detail.html', {
        'news': news, 
        'page_title': news.title
    })


@login_required
def news_create_student(request):
    """Создание новости студентом"""
    if not request.user.is_student:
        messages.error(request, 'Только студенты могут создавать объявления')
        return redirect('students:news_list')
    
    form = NewsForm(request.POST or None, request.FILES or None, user=request.user)
    
    if request.method == 'POST' and form.is_valid():
        obj = form.save(commit=False)
        obj.created_by = request.user
        
        # Студенты не могут публиковать напрямую
        obj.is_published = False
        obj.audience = 'students'  # Студенты могут создавать только для студентов
        
        # Устанавливаем организацию
        if hasattr(request.user, 'student_profile') and request.user.student_profile.organization:
            obj.organization = request.user.student_profile.organization
        
        obj.save()
        messages.success(request, 'Объявление отправлено на модерацию. Оно будет опубликовано после проверки администратором.')
        return redirect('students:news_list')
    
    return render(request, 'students/news/create.html', {
        'form': form, 
        'page_title': 'Создать объявление'
    })


@login_required
def news_list_mentor(request):
    user = request.user
    if user.role == 'mentor':
        news = News.objects.filter(is_published=True, audience__in=['all', 'mentors'])
    else:
        news = News.objects.filter(is_published=True)
    return render(request, 'mentor/news/list.html', {'news': news, 'page_title': 'Объявления'})


@login_required
def news_detail_mentor(request, pk):
    news = get_object_or_404(News, pk=pk, is_published=True)
    return render(request, 'mentor/news/detail.html', {'news': news, 'page_title': news.title})
