# Обновлённые views для использования KPI шаблонов

# Заменить в mentors/views.py:

@login_required
@admin_required
def mentor_list(request):
    mentors = MentorProfile.objects.select_related('user').filter(is_active=True)
    search = request.GET.get('q', '')
    
    # Фильтры
    if search:
        mentors = mentors.filter(
            Q(user__full_name__icontains=search) |
            Q(user__email__icontains=search) |
            Q(specialization__icontains=search)
        )
    
    if request.GET.get('status') == 'active':
        mentors = mentors.filter(is_active=True)
    elif request.GET.get('status') == 'inactive':
        mentors = mentors.filter(is_active=False)
        
    if request.GET.get('kpi_status'):
        mentors = mentors.filter(kpi_status=request.GET.get('kpi_status'))
    
    context = {
        'mentors': mentors, 
        'search': search, 
        'page_title': 'Менторы - KPI'
    }
    return render(request, 'admin/mentors/list_with_kpi.html', context)


@login_required
@admin_required
def mentor_detail(request, pk):
    profile = get_object_or_404(MentorProfile, pk=pk)
    courses = profile.user.mentor_courses.filter(is_archived=False)
    from apps.salaries.models import SalaryAccrual
    salary_history = SalaryAccrual.objects.filter(mentor=profile.user).order_by('-month')[:12]
    
    context = {
        'profile': profile,
        'courses': courses,
        'salary_history': salary_history,
        'page_title': f'{profile.get_display_name()} - KPI',
    }
    return render(request, 'admin/mentors/detail_with_kpi.html', context)
