from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q, Sum
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from apps.accounts.models import CustomUser
from apps.students.models import Student
from apps.courses.models import Course, CourseStudent
from .models import (
    CoinWallet, CoinTransaction, CoinWithdrawalSetting,
    CoinWithdrawalRequest, CoinScale, CoinBatch, CoinBatchItem
)
from .services import CoinService
from .forms import (
    WithdrawalRequestForm, BalanceAdjustmentForm, WithdrawalReviewForm,
    CoinScaleForm, CoinBatchForm, CoinMassAccrualForm, NextWithdrawalDateForm
)


def is_admin(user):
    """Проверка на админа"""
    return user.is_authenticated and user.is_admin


def is_mentor(user):
    """Проверка на ментора"""
    return user.is_authenticated and user.is_mentor


def is_student(user):
    """Проверка на студента"""
    return user.is_authenticated and user.is_student


# ==================== АДМИНСКИЙ РАЗДЕЛ ====================

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    """Главная страница админки кодкойнов"""
    setting = CoinService.get_withdrawal_setting()
    pending_requests = CoinService.get_pending_withdrawal_requests()
    recent_transactions = CoinService.get_all_transactions(limit=20)
    
    context = {
        'setting': setting,
        'pending_requests': pending_requests,
        'recent_transactions': recent_transactions,
        'total_pending': pending_requests.count(),
    }
    return render(request, 'codecoins/admin/dashboard.html', context)


@login_required
@user_passes_test(is_admin)
def admin_transactions(request):
    """Все транзакции кодкойнов"""
    search = request.GET.get('search', '')
    transaction_type = request.GET.get('type', '')
    student_id = request.GET.get('student', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    transactions = CoinTransaction.objects.filter(is_cancelled=False)
    
    # Фильтры
    if search:
        transactions = transactions.filter(
            Q(wallet__student__full_name__icontains=search) |
            Q(description__icontains=search)
        )
    
    if transaction_type:
        transactions = transactions.filter(transaction_type=transaction_type)
    
    if student_id:
        transactions = transactions.filter(wallet__student_id=student_id)
    
    if date_from:
        transactions = transactions.filter(created_at__date__gte=date_from)
    
    if date_to:
        transactions = transactions.filter(created_at__date__lte=date_to)
    
    # Пагинация
    paginator = Paginator(transactions.order_by('-created_at'), 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Форма корректировки
    adjustment_form = BalanceAdjustmentForm()
    
    context = {
        'page_obj': page_obj,
        'adjustment_form': adjustment_form,
        'transaction_types': CoinTransaction.TRANSACTION_TYPES,
    }
    return render(request, 'codecoins/admin/transactions.html', context)


@login_required
@user_passes_test(is_admin)
@require_POST
def admin_adjust_balance(request):
    """Корректировка баланса студента"""
    form = BalanceAdjustmentForm(request.POST)
    if form.is_valid():
        student = form.cleaned_data['student']
        adjustment_type = form.cleaned_data['adjustment_type']
        amount = form.cleaned_data['amount']
        reason = form.cleaned_data['reason']
        
        if adjustment_type == 'subtract':
            amount = -amount
        
        try:
            CoinService.adjust_student_balance(student, amount, reason, request.user)
            messages.success(request, f'Баланс студента {student.full_name} скорректирован')
        except Exception as e:
            messages.error(request, f'Ошибка: {str(e)}')
    else:
        messages.error(request, 'Проверьте правильность данных')
    
    return redirect('codecoins:admin_transactions')


@login_required
@user_passes_test(is_admin)
def admin_withdrawal_requests(request):
    """Заявки на вывод"""
    status_filter = request.GET.get('status', '')
    
    requests = CoinWithdrawalRequest.objects.all()
    
    if status_filter:
        requests = requests.filter(status=status_filter)
    
    requests = requests.select_related('student', 'reviewed_by').order_by('-created_at')
    
    context = {
        'requests': requests,
        'status_choices': CoinWithdrawalRequest.STATUS_CHOICES,
    }
    return render(request, 'codecoins/admin/withdrawal_requests.html', context)


@login_required
@user_passes_test(is_admin)
@require_POST
def admin_process_withdrawal(request, request_id):
    """Обработка заявки на вывод"""
    withdrawal_request = get_object_or_404(CoinWithdrawalRequest, id=request_id)
    action = request.POST.get('action')
    
    if action == 'approve':
        try:
            CoinService.approve_withdrawal_request(withdrawal_request, request.user)
            messages.success(request, 'Заявка подтверждена')
        except Exception as e:
            messages.error(request, f'Ошибка: {str(e)}')
    elif action == 'reject':
        form = WithdrawalReviewForm(request.POST)
        if form.is_valid():
            reason = form.cleaned_data['rejection_reason']
            try:
                CoinService.reject_withdrawal_request(withdrawal_request, request.user, reason)
                messages.success(request, 'Заявка отклонена')
            except Exception as e:
                messages.error(request, f'Ошибка: {str(e)}')
        else:
            messages.error(request, 'Укажите причину отклонения')
    
    return redirect('codecoins:admin_withdrawal_requests')


@login_required
@user_passes_test(is_admin)
@require_POST
def admin_toggle_withdrawal(request):
    """Переключение статуса вывода"""
    action = request.POST.get('action')
    
    if action == 'open':
        CoinService.open_withdrawal(request.user)
        messages.success(request, 'Вывод кодкойнов открыт')
    elif action == 'close':
        CoinService.close_withdrawal(request.user)
        messages.success(request, 'Вывод кодкойнов закрыт')
    
    return redirect('codecoins:admin_dashboard')


@login_required
@user_passes_test(is_admin)
def admin_set_next_withdrawal_date(request):
    """Установка даты следующего вывода"""
    if request.method == 'POST':
        form = NextWithdrawalDateForm(request.POST)
        if form.is_valid():
            next_open_at = form.cleaned_data['next_open_at']
            CoinService.close_withdrawal(request.user, next_open_at)
            messages.success(request, f'Следующее открытие вывода: {next_open_at}')
            return redirect('codecoins:admin_dashboard')
    else:
        form = NextWithdrawalDateForm()
    
    return render(request, 'codecoins/admin/set_next_date.html', {'form': form})


@login_required
@user_passes_test(is_admin)
def admin_cancel_transaction(request, transaction_id):
    """Отмена транзакции"""
    transaction = get_object_or_404(CoinTransaction, id=transaction_id)
    
    if request.method == 'POST':
        reason = request.POST.get('reason', '')
        try:
            CoinService.cancel_transaction(transaction, request.user, reason)
            messages.success(request, 'Транзакция отменена')
        except Exception as e:
            messages.error(request, f'Ошибка: {str(e)}')
        
        return redirect('codecoins:admin_transactions')
    
    return render(request, 'codecoins/admin/cancel_transaction.html', {'transaction': transaction})


# ==================== УПРАВЛЕНИЕ ШКАЛАМИ ====================

class CoinScaleListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Список шкал кодкойнов"""
    model = CoinScale
    template_name = 'codecoins/admin/scales/list.html'
    context_object_name = 'scales'
    
    def test_func(self):
        return self.request.user.is_admin
    
    def get_queryset(self):
        return CoinScale.objects.all().order_by('sort_order')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_scales_count'] = CoinScale.objects.filter(is_active=True).count()
        return context


class CoinScaleCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Создание шкалы кодкойнов"""
    model = CoinScale
    form_class = CoinScaleForm
    template_name = 'codecoins/admin/scales/form.html'
    success_url = reverse_lazy('codecoins:admin_scales')
    
    def test_func(self):
        return self.request.user.is_admin
    
    def form_valid(self, form):
        messages.success(self.request, 'Шкала создана')
        return super().form_valid(form)


class CoinScaleUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Редактирование шкалы кодкойнов"""
    model = CoinScale
    form_class = CoinScaleForm
    template_name = 'codecoins/admin/scales/form.html'
    success_url = reverse_lazy('codecoins:admin_scales')
    
    def test_func(self):
        return self.request.user.is_admin
    
    def form_valid(self, form):
        messages.success(self.request, 'Шкала обновлена')
        return super().form_valid(form)


class CoinScaleDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Удаление шкалы кодкойнов"""
    model = CoinScale
    template_name = 'codecoins/admin/scales/delete.html'
    success_url = reverse_lazy('codecoins:admin_scales')
    
    def test_func(self):
        return self.request.user.is_admin
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Шкала удалена')
        return super().delete(request, *args, **kwargs)


# ==================== РАЗДЕЛ СТУДЕНТА ====================

@login_required
@user_passes_test(is_student)
def student_dashboard(request):
    """Личный кабинет студента - кодкойны"""
    student = request.user.student_profile
    
    # Получаем баланс
    balance = CoinService.get_student_balance(student)
    
    # Получаем настройки вывода
    setting = CoinService.get_withdrawal_setting()
    
    # Получаем историю транзакций
    transactions = CoinService.get_student_transaction_history(student, limit=10)
    
    # Получаем историю выводов
    withdrawals = CoinService.get_student_withdrawal_history(student)
    
    # Форма заявки на вывод
    withdrawal_form = None
    if setting.is_open and balance >= 100:
        withdrawal_form = WithdrawalRequestForm(student)
    
    context = {
        'student': student,
        'balance': balance,
        'setting': setting,
        'transactions': transactions,
        'withdrawals': withdrawals,
        'withdrawal_form': withdrawal_form,
    }
    return render(request, 'codecoins/student/dashboard.html', context)


@login_required
@user_passes_test(is_student)
def student_create_withdrawal_request(request):
    """Создание заявки на вывод"""
    student = request.user.student_profile
    
    if request.method == 'POST':
        form = WithdrawalRequestForm(student, request.POST)
        if form.is_valid():
            try:
                withdrawal_request = CoinService.create_withdrawal_request(
                    student=student,
                    amount=form.cleaned_data['amount'],
                    payout_method=form.cleaned_data['payout_method'],
                    phone_number=form.cleaned_data['phone_number'],
                    comment=form.cleaned_data['comment']
                )
                messages.success(request, 'Заявка на вывод отправлена')
                return redirect('codecoins:student_dashboard')
            except Exception as e:
                messages.error(request, f'Ошибка: {str(e)}')
        else:
            messages.error(request, 'Проверьте правильность данных')
    
    return redirect('codecoins:student_dashboard')


@login_required
@user_passes_test(is_student)
def student_transactions(request):
    """История транзакций студента"""
    student = request.user.student_profile
    
    transactions = CoinService.get_student_transaction_history(student)
    
    # Пагинация
    paginator = Paginator(transactions, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'codecoins/student/transactions.html', context)


@login_required
@user_passes_test(is_student)
def student_withdrawals(request):
    """История выводов студента"""
    student = request.user.student_profile
    
    withdrawals = CoinService.get_student_withdrawal_history(student)
    
    # Пагинация
    paginator = Paginator(withdrawals, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'codecoins/student/withdrawals.html', context)


# ==================== РАЗДЕЛ МЕНТОРА ====================

@login_required
@user_passes_test(is_mentor)
def mentor_course_codecoins(request, course_id):
    """Кодкойны в кабинете курса ментора"""
    course = get_object_or_404(Course, id=course_id, mentor=request.user)
    
    # Получаем студентов курса
    course_students = CourseStudent.objects.filter(
        course=course, status='active'
    ).select_related('student')
    
    # Получаем активные шкалы
    scales = CoinService.get_active_scales()
    
    # Получаем последние пакеты начислений
    recent_batches = CoinBatch.objects.filter(
        course=course
    ).select_related('mentor').order_by('-lesson_date')[:5]
    
    context = {
        'course': course,
        'course_students': course_students,
        'scales': scales,
        'recent_batches': recent_batches,
    }
    return render(request, 'codecoins/mentor/course_dashboard.html', context)


@login_required
@user_passes_test(is_mentor)
def mentor_create_batch(request, course_id):
    """Создание пакета начислений"""
    course = get_object_or_404(Course, id=course_id, mentor=request.user)
    
    if request.method == 'POST':
        form = CoinBatchForm(course, request.POST)
        if form.is_valid():
            batch = CoinService.create_coin_batch(
                course=course,
                mentor=request.user,
                lesson_date=form.cleaned_data['lesson_date'],
                comment=form.cleaned_data['comment']
            )
            messages.success(request, f'Пакет для {form.cleaned_data["lesson_date"]} создан')
            return redirect('codecoins_mentor:mentor_mass_accrual', course_id=course.id, batch_id=batch.id)
    else:
        form = CoinBatchForm(course)
    
    # Получаем студентов курса
    students = CourseStudent.objects.filter(
        course=course, 
        status='active'
    ).select_related('student')
    
    # Получаем активные шкалы
    scales = CoinScale.objects.filter(is_active=True).order_by('sort_order')
    
    context = {
        'course': course,
        'form': form,
        'students': [cs.student for cs in students],
        'scales': scales,
    }
    return render(request, 'codecoins/mentor/create_batch.html', context)


@login_required
@user_passes_test(is_mentor)
def mentor_mass_accrual(request, course_id, batch_id):
    """Массовое начисление кодкойнов"""
    course = get_object_or_404(Course, id=course_id, mentor=request.user)
    batch = get_object_or_404(CoinBatch, id=batch_id, course=course)
    
    # Получаем студентов курса
    course_students = CourseStudent.objects.filter(
        course=course, status='active'
    ).select_related('student')
    
    # Получаем активные шкалы
    scales = CoinService.get_active_scales()
    
    if request.method == 'POST':
        form = CoinMassAccrualForm(course_students, scales, request.POST)
        if form.is_valid():
            # Очищаем существующие элементы
            batch.items.all().delete()
            
            # Добавляем новые элементы
            for student in course_students:
                for scale in scales:
                    field_name = f"student_{student.id}_scale_{scale.id}"
                    if form.cleaned_data.get(field_name):
                        CoinService.add_batch_item(
                            batch=batch,
                            student=student.student,
                            scale=scale,
                            description=f'{scale.title} - {student.student.full_name}'
                        )
            
            # Применяем пакет
            CoinService.apply_coin_batch(batch, request.user)
            
            messages.success(request, f'Начисления для урока {batch.lesson_date} применены')
            return redirect('codecoins_mentor:mentor_course_codecoins', course_id=course.id)
    else:
        form = CoinMassAccrualForm(course_students, scales)
    
    context = {
        'course': course,
        'batch': batch,
        'students': [cs.student for cs in course_students],
        'total_students': course_students.count(),
        'scales': scales,
        'form': form,
    }
    return render(request, 'codecoins/mentor/mass_accrual.html', context)


# AJAX Views
@login_required
@user_passes_test(is_student)
def ajax_student_balance(request):
    """AJAX получение баланса студента"""
    if request.user.is_student:
        student = request.user.student_profile
        balance = CoinService.get_student_balance(student)
        return JsonResponse({'balance': str(balance)})
    return JsonResponse({'error': 'Unauthorized'}, status=401)
