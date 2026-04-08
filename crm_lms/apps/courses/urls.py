from django.urls import path
from . import views
from . import views_admin
from . import views_tariffs
from . import views_tariffs_extra

app_name = 'courses'

urlpatterns = [
    path('', views.course_list, name='list'),
    path('archive/', views.course_archive, name='archive'),
    path('create/', views.course_create, name='create'),
    path('<int:pk>/', views.course_detail, name='detail'),
    path('<int:pk>/edit/', views.course_edit, name='edit'),
    path('<int:pk>/delete/', views.course_delete, name='delete'),
    path('<int:pk>/extend/', views.course_extend, name='extend'),
    path('<int:pk>/add-student/', views.course_add_student, name='add_student'),
    path('enrollment/<int:pk>/remove/', views.remove_student, name='remove_student'),
    path('student-drawer/<int:pk>/', views.student_drawer, name='student_drawer'),
    
    # Quick attendance and ticket adjustment URLs
    path('<int:pk>/mark-attendance/', views.mark_attendance_quick, name='mark_attendance_quick'),
    path('<int:pk>/adjust-tickets/', views.adjust_tickets_ajax, name='adjust_tickets'),
    
    # Excel export URLs
    path('<int:pk>/student-excel/<int:enrollment_id>/', views.student_excel_export, name='student_excel_export'),
    path('<int:pk>/overall-excel/', views.overall_excel_export, name='overall_excel_export'),
    path('<int:pk>/unlimited-excel/', views.unlimited_course_excel_export, name='unlimited_course_excel_export'),
    
    # Ticket URLs
    path('tickets/add/<int:cs_pk>/', views.add_tickets, name='add_tickets'),
    path('tickets/mark-attendance/<int:cs_pk>/', views.mark_attendance, name='mark_attendance'),
    path('tickets/history/<int:cs_pk>/', views.ticket_history, name='ticket_history'),
    path('tickets/adjust/<int:cs_pk>/', views.adjust_tickets, name='adjust_tickets'),
    
    # Admin API URLs
    path('student-details/<int:cs_id>/', views_admin.student_details_api, name='student_details_api'),
    path('tariffs-api/', views_admin.tariffs_api, name='tariffs_api'),
    path('tariff/<int:tariff_id>/', views_admin.tariff_detail_api, name='tariff_detail_api'),
    path('add-tickets/', views_admin.add_tickets_api, name='add_tickets_api'),
    path('ticket-history/<int:cs_id>/', views_admin.ticket_history_api, name='ticket_history_api'),
    
    # Tariffs Management URLs
    path('tariffs/create/', views_tariffs.create_tariff, name='create_tariff'),
    path('tariffs/<int:tariff_id>/data/', views_tariffs_extra.get_tariff_data, name='get_tariff_data'),
    path('tariffs/<int:tariff_id>/update/', views_tariffs.update_tariff, name='update_tariff'),
    path('tariffs/<int:tariff_id>/delete/', views_tariffs.delete_tariff, name='delete_tariff'),
    path('tariffs/<int:tariff_id>/toggle/', views_tariffs.toggle_tariff, name='toggle_tariff'),
    path('tariffs/', views_tariffs.tariffs_list, name='tariffs_list'),
]
