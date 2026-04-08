from django.urls import path
from . import views

app_name = 'codecoins'

urlpatterns = [
    # Административный раздел
    path('admin/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/transactions/', views.admin_transactions, name='admin_transactions'),
    path('admin/adjust-balance/', views.admin_adjust_balance, name='admin_adjust_balance'),
    path('admin/withdrawal-requests/', views.admin_withdrawal_requests, name='admin_withdrawal_requests'),
    path('admin/process-withdrawal/<int:request_id>/', views.admin_process_withdrawal, name='admin_process_withdrawal'),
    path('admin/toggle-withdrawal/', views.admin_toggle_withdrawal, name='admin_toggle_withdrawal'),
    path('admin/set-next-date/', views.admin_set_next_withdrawal_date, name='admin_set_next_date'),
    path('admin/cancel-transaction/<int:transaction_id>/', views.admin_cancel_transaction, name='admin_cancel_transaction'),
    
    # Управление шкалами
    path('admin/scales/', views.CoinScaleListView.as_view(), name='admin_scales'),
    path('admin/scales/create/', views.CoinScaleCreateView.as_view(), name='admin_scale_create'),
    path('admin/scales/<int:pk>/edit/', views.CoinScaleUpdateView.as_view(), name='admin_scale_edit'),
    path('admin/scales/<int:pk>/delete/', views.CoinScaleDeleteView.as_view(), name='admin_scale_delete'),
    
    # Раздел студента
    path('student/', views.student_dashboard, name='student_dashboard'),
    path('student/withdrawal-request/', views.student_create_withdrawal_request, name='student_create_withdrawal_request'),
    path('student/transactions/', views.student_transactions, name='student_transactions'),
    path('student/withdrawals/', views.student_withdrawals, name='student_withdrawals'),
    
    # Раздел ментора
    path('mentor/course/<int:course_id>/', views.mentor_course_codecoins, name='mentor_course_codecoins'),
    path('mentor/course/<int:course_id>/create-batch/', views.mentor_create_batch, name='mentor_create_batch'),
    path('mentor/course/<int:course_id>/batch/<int:batch_id>/', views.mentor_mass_accrual, name='mentor_mass_accrual'),
    
    # AJAX
    path('ajax/student-balance/', views.ajax_student_balance, name='ajax_student_balance'),
]
