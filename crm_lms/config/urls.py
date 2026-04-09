from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from apps.core.views import create_admin_once

from apps.reviews.views import feedback_form as public_feedback_form
from apps.core.views import custom_404, custom_500, custom_403
from apps.leads import views as leads_views
from apps.students.views import student_info_page


def health(request):
    return HttpResponse("ok")


def test_attendance_view(request):
    return JsonResponse({'success': True, 'message': 'Direct URL works!'})


@csrf_exempt
@require_POST
@login_required
def temp_save_attendance(request, course_id):
    from apps.attendance.models import AttendanceRecord
    from apps.courses.models import Course
    from apps.courses.services import TicketService
    from apps.lessons.models import Lesson

    try:
        if not request.user.is_authenticated:
            return JsonResponse({'success': False, 'error': 'Not authenticated'})

        course = Course.objects.get(pk=course_id)

        for key, value in request.POST.items():
            if key.startswith('att_'):
                parts = key.split('_')
                if len(parts) == 3:
                    lesson_id = int(parts[1])
                    student_id = int(parts[2])

                    AttendanceRecord.objects.update_or_create(
                        lesson_id=lesson_id,
                        student_id=student_id,
                        defaults={
                            'attendance_status': value,
                            'marked_by': request.user if value else None,
                            'color_status': value if value else ''
                        },
                    )

        return JsonResponse({'success': True})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


urlpatterns = [
    path('health/', health),
    path('create-admin-once/', create_admin_once),

    # вот этого у тебя не хватало
    path('i18n/', include('django.conf.urls.i18n')),

    path('mentor/courses/<int:course_id>/attendance/save/', temp_save_attendance),
    path('mentor/attendance-direct-test/', test_attendance_view),

    path('django-admin/', admin.site.urls),

    path('auth/lockout/', TemplateView.as_view(template_name='auth/lockout.html'), name='axes_lockout'),

    path('accounts/', include('apps.accounts.urls', namespace='accounts')),
    path('dashboard/', include('apps.dashboard.urls', namespace='dashboard')),
    path('analytics/', include('apps.dashboard.urls_analytics', namespace='analytics')),
    path('manager/', include('apps.manager.urls', namespace='manager')),
    path('organizations/', include('apps.organizations.urls', namespace='organizations')),

    path('admin/news/', include('apps.news.urls', namespace='news')),
    path('admin/courses/', include('apps.courses.urls', namespace='courses')),
    path('admin/students/', include('apps.students.urls', namespace='admin_students')),
    path('admin/mentors/', include('apps.mentors.urls', namespace='mentors')),
    path('admin/payments/', include('apps.payments.urls', namespace='payments')),
    path('admin/debts/', include('apps.debts.urls', namespace='debts')),
    path('admin/salaries/', include('apps.salaries.urls', namespace='salaries')),
    path('admin/leads/', include('apps.leads.urls', namespace='leads')),
    path('admin/finance/', include('apps.finance.urls', namespace='finance')),
    path('admin/reports/', include('apps.reports.urls', namespace='reports')),
    path('admin/settings/', include('apps.settings.urls', namespace='settings')),
    path('admin/organizations/', include('apps.organizations.urls', namespace='organizations')),
    path('admin/codecoins/', include('apps.codecoins.urls', namespace='codecoins_admin')),
    path('admin/chat/', include('apps.chat.urls_admin', namespace='chat_admin')),

    path('calendar/', include('apps.calendar_app.urls', namespace='calendar_app')),

    path('form/<uuid:unique_id>/', leads_views.public_form, name='public_form'),
    path('form/<uuid:unique_id>/submit/', leads_views.form_submit, name='form_submit'),
    path('form/<uuid:unique_id>/success/', leads_views.form_success, name='form_success'),

    path('admin/', include('apps.lessons.urls_admin', namespace='admin_lessons')),

    path('mentor/', include('apps.attendance.urls', namespace='attendance')),
    path('lms/mentor/', include('apps.attendance.urls', namespace='attendance')),

    path('mentor/', include('apps.quizzes.urls', namespace='quizzes')),
    path('lms/mentor/', include('apps.quizzes.urls', namespace='quizzes')),

    path('mentor/', include('apps.lectures.urls', namespace='lectures')),
    path('lms/mentor/', include('apps.lectures.urls', namespace='lectures')),

    path('mentor/', include('apps.assignments.urls', namespace='assignments')),
    path('lms/mentor/', include('apps.assignments.urls', namespace='assignments')),

    path('mentor/', include('apps.lessons.urls', namespace='lessons')),
    path('lms/mentor/', include('apps.lessons.urls', namespace='lessons')),

    path('mentor/', include('apps.rating.urls', namespace='rating')),
    path('lms/mentor/', include('apps.rating.urls', namespace='rating')),

    path('mentor/', include('apps.reviews.urls', namespace='reviews')),
    path('lms/mentor/', include('apps.reviews.urls', namespace='reviews')),

    path('mentor/', include('apps.codecoins.urls', namespace='codecoins_mentor')),
    path('lms/mentor/', include('apps.codecoins.urls', namespace='codecoins_mentor')),

    path('notifications/', include('apps.notifications.urls', namespace='notifications')),
    path('feedback/', include('apps.feedback.urls', namespace='feedback')),
    path('chat/', include('apps.chat.urls', namespace='chat')),

    path('student/', include('apps.students_portal.urls', namespace='students')),
    path('lms/student/', include('apps.codecoins.urls', namespace='codecoins_student')),

    path('common/student-info/<int:student_id>/', student_info_page, name='student_info_page'),

    path('api/v1/', include('apps.core.api_urls', namespace='api')),

    path('', include('apps.core.urls', namespace='core')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = 'apps.core.views.custom_404'
handler500 = 'apps.core.views.custom_500'
handler403 = 'apps.core.views.custom_403'
