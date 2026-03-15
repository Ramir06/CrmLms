from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone

from apps.core.mixins import admin_required
from .models import News


class NewsForm:
    pass


from django import forms


class NewsForm(forms.ModelForm):
    class Meta:
        model = News
        fields = ['title', 'content', 'image', 'audience', 'is_published']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 6}),
            'audience': forms.Select(attrs={'class': 'form-select'}),
        }


@login_required
@admin_required
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
