from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from apps.core.mixins import admin_required
from .models import Lead, LeadAction


from django import forms


class LeadForm(forms.ModelForm):
    class Meta:
        model = Lead
        fields = ['full_name', 'phone', 'source', 'interested_course',
                  'channel', 'assigned_to', 'status', 'note']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'source': forms.Select(attrs={'class': 'form-select'}),
            'interested_course': forms.Select(attrs={'class': 'form-select'}),
            'channel': forms.TextInput(attrs={'class': 'form-control'}),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


KANBAN_COLUMNS = [
    ('new', 'Новый', 'bg-secondary'),
    ('consultation', 'Консультация', 'bg-info'),
    ('trial_lesson', 'Пробный урок', 'bg-primary'),
    ('no_show', 'Не пришёл', 'bg-warning'),
    ('enrolling', 'Зачисление', 'bg-success'),
    ('rejected', 'Отказ', 'bg-danger'),
]


@login_required
@admin_required
def lead_kanban(request):
    leads_by_status = {}
    for status, label, color in KANBAN_COLUMNS:
        leads_by_status[status] = {
            'label': label,
            'color': color,
            'leads': Lead.objects.filter(status=status, is_archived=False)
                       .select_related('interested_course', 'assigned_to')
                       .order_by('-created_at'),
        }

    form = LeadForm()
    context = {
        'leads_by_status': leads_by_status,
        'kanban_columns': KANBAN_COLUMNS,
        'form': form,
        'page_title': 'CRM Лиды',
    }
    return render(request, 'admin/leads/kanban.html', context)


@login_required
@admin_required
def lead_create(request):
    form = LeadForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        lead = form.save()
        LeadAction.objects.create(
            lead=lead,
            performed_by=request.user,
            new_status=lead.status,
            comment='Лид создан',
        )
        messages.success(request, f'Лид «{lead.full_name}» добавлен.')
        return redirect('leads:kanban')
    return render(request, 'admin/leads/form.html', {'form': form, 'page_title': 'Добавить лид'})


@login_required
@admin_required
def lead_detail(request, pk):
    lead = get_object_or_404(Lead, pk=pk)
    actions = lead.actions.select_related('performed_by').all()[:20]
    form = LeadForm(request.POST or None, instance=lead)
    if request.method == 'POST' and form.is_valid():
        old_status = lead.status
        lead = form.save()
        if old_status != lead.status:
            LeadAction.objects.create(
                lead=lead,
                performed_by=request.user,
                old_status=old_status,
                new_status=lead.status,
                comment=f'Статус изменён: {old_status} → {lead.status}',
            )
        messages.success(request, 'Лид обновлён.')
        return redirect('leads:kanban')
    context = {'lead': lead, 'actions': actions, 'form': form, 'page_title': lead.full_name}
    return render(request, 'admin/leads/detail.html', context)


@login_required
@admin_required
@require_POST
def lead_move(request, pk):
    """Move lead to a new kanban status via POST."""
    lead = get_object_or_404(Lead, pk=pk)
    new_status = request.POST.get('status')
    valid_statuses = [s[0] for s in Lead.STATUS_CHOICES]

    if new_status in valid_statuses:
        old_status = lead.status
        lead.status = new_status
        lead.save()
        LeadAction.objects.create(
            lead=lead,
            performed_by=request.user,
            old_status=old_status,
            new_status=new_status,
            comment=f'Перемещён: {old_status} → {new_status}',
        )
        return JsonResponse({'status': 'ok', 'new_status': new_status})

    return JsonResponse({'error': 'invalid status'}, status=400)


@login_required
@admin_required
def lead_archive(request):
    leads = Lead.objects.filter(is_archived=True).order_by('-updated_at')
    return render(request, 'admin/leads/archive.html', {'leads': leads, 'page_title': 'Архив лидов'})
