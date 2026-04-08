from django.urls import path
from . import views

app_name = 'debts'

urlpatterns = [
    path('', views.debt_list, name='list'),
    path('export/', views.debt_export, name='export'),
    path('update/', views.update_debtors_api, name='update'),
    path('<int:debt_id>/block/', views.block_student_account, name='block_student'),
    path('<int:debt_id>/pay/', views.pay_debt, name='pay_debt'),
]
