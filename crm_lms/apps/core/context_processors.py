from apps.notifications.models import Notification


def global_context(request):
    context = {}
    if request.user.is_authenticated:
        context['unread_notifications_count'] = Notification.objects.filter(
            recipient=request.user, is_read=False
        ).count()
        context['current_role'] = request.user.role
        context['is_admin_role'] = request.user.role in ('admin', 'superadmin')
        context['is_mentor_role'] = request.user.role == 'mentor'
        context['is_student_role'] = request.user.role == 'student'
        
        # Добавляем текущую организацию
        if hasattr(request, 'current_organization'):
            context['current_organization'] = request.current_organization
        else:
            # Fallback: пытаемся получить организацию
            try:
                from .mixins import get_current_organization
                context['current_organization'] = get_current_organization(request.user)
            except:
                context['current_organization'] = None
        
        if request.user.role in ('mentor', 'admin', 'superadmin'):
            from apps.courses.models import Course
            context['my_courses'] = Course.objects.filter(
                mentor=request.user, is_archived=False
            ).order_by('title')
        if request.user.role == 'student':
            student_profile = getattr(request.user, 'student_profile', None)
            if student_profile:
                from apps.courses.models import CourseStudent
                context['enrollments'] = CourseStudent.objects.filter(
                    student=student_profile, status='active'
                ).select_related('course', 'course__mentor').order_by('-joined_at')
    return context
