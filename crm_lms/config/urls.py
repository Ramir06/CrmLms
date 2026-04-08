from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from apps.reviews.views import feedback_form as public_feedback_form
from apps.core.views import custom_404, custom_500, custom_403
from apps.leads import views as leads_views
from apps.students.views import student_info_page

# Временный тестовый URL для проверки работы
def test_attendance_view(request):
    from django.http import JsonResponse
    return JsonResponse({'success': True, 'message': 'Direct URL works!'})

# Временная view для сохранения посещаемости
@csrf_exempt
@require_POST
@login_required
def temp_save_attendance(request, course_id):
    from django.http import JsonResponse
    from apps.attendance.models import AttendanceRecord
    from apps.courses.models import Course, CourseStudent
    from apps.courses.services import TicketService
    from apps.lessons.models import Lesson
    import json
    
    print(f"!!! TEMP SAVE ATTENDANCE CALLED !!!", flush=True)
    print(f"!!! COURSE ID: {course_id} !!!", flush=True)
    print(f"!!! METHOD: {request.method} !!!", flush=True)
    print(f"!!! USER: {request.user.username if request.user.is_authenticated else 'anonymous'} !!!", flush=True)
    print(f"!!! POST DATA: {dict(request.POST)} !!!", flush=True)
    
    if request.method == 'POST':
        try:
            # Проверяем авторизацию
            if not request.user.is_authenticated:
                return JsonResponse({'success': False, 'error': 'Not authenticated'})
            
            # Получаем курс
            course = Course.objects.get(pk=course_id)
            
            processed_lessons = []
            
            # Обрабатываем все данные из POST
            for key, value in request.POST.items():
                if key.startswith('att_'):
                    parts = key.split('_')
                    if len(parts) == 3:
                        try:
                            lesson_id = int(parts[1])
                            student_id = int(parts[2])
                            
                            print(f"Processing: lesson {lesson_id}, student {student_id}, value: {value}", flush=True)
                            
                            # Сохраняем запись о посещаемости
                            attendance_record, created = AttendanceRecord.objects.update_or_create(
                                lesson_id=lesson_id,
                                student_id=student_id,
                                defaults={
                                    'attendance_status': value, 
                                    'marked_by': request.user if value else None,
                                    'color_status': value if value else ''
                                },
                            )
                            
                            print(f"Saved: created={created}, status='{attendance_record.attendance_status}'", flush=True)
                            
                            # Отладочная информация
                            print(f"Debug: value='{value}', course.is_unlimited={course.is_unlimited}", flush=True)
                            
                            # Если это бесконечный курс и статус "present", списываем талон
                            if value == 'present' and course.is_unlimited:
                                print(f"Processing ticket deduction for unlimited course", flush=True)
                                try:
                                    cs = CourseStudent.objects.get(
                                        course=course,
                                        student_id=student_id,
                                        status='active'
                                    )
                                    lesson = Lesson.objects.get(pk=lesson_id)
                                    
                                    # Списываем талон и создаем TicketAttendance
                                    transaction_obj, attendance = TicketService.consume_tickets(
                                        enrollment=cs,
                                        lessons_count=1,
                                        marked_by=request.user,
                                        lesson_date=lesson.lesson_date,
                                        comment=f"Посещение урока {lesson_id}"
                                    )
                                    print(f"Ticket deducted: transaction={transaction_obj.id}, attendance={attendance.id}", flush=True)
                                except Exception as e:
                                    print(f"Error deducting ticket: {str(e)}", flush=True)
                            
                            if lesson_id not in processed_lessons:
                                processed_lessons.append(lesson_id)
                                
                        except Exception as e:
                            print(f"Error processing {key}: {str(e)}", flush=True)
                            continue
            
            return JsonResponse({
                'success': True, 
                'debug': {
                    'processed_lessons': processed_lessons,
                    'course_id': course_id,
                    'user': request.user.username
                }
            })
            
        except Exception as e:
            print(f"ERROR: {str(e)}", flush=True)
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Method not allowed'})

urlpatterns = [
    # Временный URL для теста сохранения посещаемости - должен быть ВЫШЕ include attendance
    path('mentor/courses/<int:course_id>/attendance/save/', temp_save_attendance),
    path('mentor/attendance-direct-test/', test_attendance_view),
    path('i18n/', include('django.conf.urls.i18n')),
    path('django-admin/', admin.site.urls),
    
    # Axes lockout URL
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
    
    # Публичные формы лидогенерации
    path('form/<uuid:unique_id>/', leads_views.public_form, name='public_form'),
    path('form/<uuid:unique_id>/submit/', leads_views.form_submit, name='form_submit'),
    path('form/<uuid:unique_id>/success/', leads_views.form_success, name='form_success'),

    path('admin/', include('apps.lessons.urls_admin', namespace='admin_lessons')),
    
    # Mentor URLs - attendance в самом начале чтобы избежать конфликтов
    path('mentor/', include('apps.attendance.urls', namespace='attendance')),
    path('lms/mentor/', include('apps.attendance.urls', namespace='attendance')),
    
    path('lms/mentor/', include('apps.quizzes.urls', namespace='quizzes')),
    path('mentor/', include('apps.quizzes.urls', namespace='quizzes')),
    path('lms/mentor/', include('apps.quizzes.urls', namespace='quizzes')),
    path('mentor/', include('apps.lectures.urls', namespace='lectures')),
    path('lms/mentor/', include('apps.lectures.urls', namespace='lectures')),
    path('mentor/', include('apps.assignments.urls', namespace='assignments')),
    path('lms/mentor/', include('apps.assignments.urls', namespace='assignments')),
    path('mentor/', include('apps.lessons.urls', namespace='lessons')),
    path('lms/mentor/', include('apps.lessons.urls', namespace='lessons')),
    path('mentor/', include('apps.lessons.urls_substitute', namespace='lessons_substitute')),
    path('lms/mentor/', include('apps.lessons.urls_substitute', namespace='lessons_substitute')),
    path('mentor/', include('apps.rating.urls', namespace='rating')),
    path('lms/mentor/', include('apps.rating.urls', namespace='rating')),
    path('mentor/', include('apps.reviews.urls', namespace='reviews')),
    path('lms/mentor/', include('apps.reviews.urls', namespace='reviews')),
    path('mentor/', include('apps.codecoins.urls', namespace='codecoins_mentor')),
    path('lms/mentor/', include('apps.codecoins.urls', namespace='codecoins_mentor')),
    path('lms/mentor/', include('apps.mentors.urls_course', namespace='mentors')),

    path('quizzes/', include('apps.quizzes.student_urls')),

    path('notifications/', include('apps.notifications.urls', namespace='notifications')),
    
    # Обратная связь
    path('feedback/', include('apps.feedback.urls', namespace='feedback')),
    
    # Чат для администраторов, суперадминистраторов и менторов
    path('chat/', include('apps.chat.urls', namespace='chat')),

    path('student/', include('apps.students_portal.urls', namespace='students')),
    path('lms/student/', include('apps.codecoins.urls', namespace='codecoins_student')),
    
    # Информация о студенте для родителей
    path('common/student-info/<int:student_id>/', student_info_page, name='student_info_page'),

    # REST API
    path('api/v1/', include('apps.core.api_urls', namespace='api')),

    path('', include('apps.core.urls', namespace='core')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    # CKEditor media URLs in debug mode
    urlpatterns += static('ckeditor/', document_root=settings.MEDIA_ROOT)

# Custom error handlers
handler404 = 'apps.core.views.custom_404'
handler500 = 'apps.core.views.custom_500'
handler403 = 'apps.core.views.custom_403'
