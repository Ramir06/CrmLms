from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from apps.reviews.views import feedback_form as public_feedback_form
from apps.core.views import custom_404, custom_500, custom_403

urlpatterns = [
    path('i18n/', include('django.conf.urls.i18n')),
    path('django-admin/', admin.site.urls),

    path('accounts/', include('apps.accounts.urls', namespace='accounts')),
    path('dashboard/', include('apps.dashboard.urls', namespace='dashboard')),

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

    path('calendar/', include('apps.calendar_app.urls', namespace='calendar_app')),

    path('mentor/', include('apps.lectures.urls', namespace='lectures')),
    path('mentor/', include('apps.assignments.urls', namespace='assignments')),
    path('mentor/', include('apps.lessons.urls', namespace='lessons')),
    path('mentor/', include('apps.attendance.urls', namespace='attendance')),
    path('mentor/', include('apps.rating.urls', namespace='rating')),
    path('mentor/', include('apps.reviews.urls', namespace='reviews')),
    path('feedback/<uuid:token>/', public_feedback_form, name='public_feedback_form'),
    path('mentor/', include('apps.quizzes.urls', namespace='quizzes')),

    path('quizzes/', include('apps.quizzes.student_urls')),

    path('notifications/', include('apps.notifications.urls', namespace='notifications')),

    path('student/', include('apps.students_portal.urls', namespace='students')),

    path('', include('apps.core.urls', namespace='core')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Custom error handlers
handler404 = 'apps.core.views.custom_404'
handler500 = 'apps.core.views.custom_500'
handler403 = 'apps.core.views.custom_403'
