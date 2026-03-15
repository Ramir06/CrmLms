from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.db.models import Sum

from apps.core.mixins import admin_required
from .models import FinanceTransaction, FinanceCategory, FinanceAccount


from django import forms


class TransactionForm(forms.ModelForm):
    class Meta:
        model = FinanceTransaction
        fields = ['type', 'category', 'amount', 'account', 'description', 'transaction_date']
        widgets = {
            'type': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'account': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'transaction_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


@login_required
@admin_required
def finance_list(request):
    qs = FinanceTransaction.objects.select_related('category', 'account', 'created_by').all()

    type_filter = request.GET.get('type')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    if type_filter:
        qs = qs.filter(type=type_filter)
    if date_from:
        qs = qs.filter(transaction_date__gte=date_from)
    if date_to:
        qs = qs.filter(transaction_date__lte=date_to)

    total_income = qs.filter(type='income').aggregate(s=Sum('amount'))['s'] or 0
    total_expense = qs.filter(type='expense').aggregate(s=Sum('amount'))['s'] or 0
    balance = total_income - total_expense

    accounts = FinanceAccount.objects.all()
    categories = FinanceCategory.objects.all()

    context = {
        'transactions': qs[:300],
        'total_income': total_income,
        'total_expense': total_expense,
        'balance': balance,
        'accounts': accounts,
        'categories': categories,
        'page_title': 'Финансы',
        'type_filter': type_filter,
    }
    return render(request, 'admin/finance/list.html', context)


@login_required
@admin_required
def transaction_create(request):
    form = TransactionForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        tx = form.save(commit=False)
        tx.created_by = request.user
        tx.save()
        messages.success(request, 'Транзакция добавлена.')
        return redirect('finance:list')
    return render(request, 'admin/finance/form.html', {'form': form, 'page_title': 'Добавить транзакцию'})


@login_required
@admin_required
def finance_export(request):
    import openpyxl
    from django.utils import timezone
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Финансы'
    ws.append(['ID', 'Тип', 'Категория', 'Сумма', 'Счёт', 'Описание', 'Дата'])
    for t in FinanceTransaction.objects.select_related('category', 'account').all():
        ws.append([
            t.pk, t.get_type_display(),
            t.category.name if t.category else '',
            float(t.amount),
            t.account.name if t.account else '',
            t.description,
            str(t.transaction_date),
        ])
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename=finance_{timezone.now().strftime("%Y%m%d")}.xlsx'
    wb.save(response)
    return response
