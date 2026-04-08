from apps.notifications.models import Notification

def notification_context(request):
    """Add unread notifications count to context for all templates."""
    if request.user.is_authenticated and request.user.is_student:
        unread_count = Notification.objects.filter(
            recipient=request.user,
            is_read=False
        ).count()
        return {
            'unread_count': unread_count
        }
    return {'unread_count': 0}


def student_course_context(request):
    """Add current course to context for student navigation."""
    course = None
    
    # Check if we're on a course detail page and extract course ID
    if request.user.is_authenticated and request.user.is_student:
        # Try to get course from URL pattern like /student/courses/49/
        path_parts = request.path.strip('/').split('/')
        if len(path_parts) >= 3 and path_parts[0] == 'student' and path_parts[1] == 'courses':
            try:
                course_id = int(path_parts[2])
                from apps.courses.models import Course
                course = Course.objects.filter(pk=course_id).first()
            except (ValueError, IndexError):
                pass
    
    return {'course': course}
