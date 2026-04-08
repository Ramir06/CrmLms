import json

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Count, Q, Max, Sum
from django.utils import timezone
from django import forms
from django.urls import reverse
import json

# Импортируем простую форму
from .forms import SimpleLeadForm
from .models import Lead, LeadGenerationForm, LeadFormField, FormSubmission, FormFieldValue
from apps.core.mixins import get_current_organization, organization_context

KANBAN_COLUMNS = [
    ('new', 'Новый', 'bg-secondary'),
    ('consultation', 'Консультация', 'bg-info'),
    ('trial_lesson', 'Пробный урок', 'bg-primary'),
    ('no_show', 'Не пришёл', 'bg-warning'),
    ('enrolling', 'Зачисление', 'bg-success'),
    ('rejected', 'Отказ', 'bg-danger'),
]


@csrf_exempt
@require_POST
def bulk_delete_leads(request):
    """Массовое удаление лидов"""
    try:
        data = json.loads(request.body)
        lead_ids = data.get('lead_ids', [])
        
        if not lead_ids:
            return JsonResponse({'success': False, 'error': 'Не выбраны лиды для удаления'})
        
        # Удаляем лиды
        deleted_count = Lead.objects.filter(pk__in=lead_ids).delete()[0]
        
        return JsonResponse({
            'success': True,
            'message': f'Удалено {deleted_count} лид(а/ов)'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Неверные данные запроса'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@csrf_exempt
@require_POST
def delete_status_leads(request):
    """Удаление всех лидов в конкретном статусе"""
    try:
        data = json.loads(request.body)
        status_slug = data.get('status_slug')
        
        if not status_slug:
            return JsonResponse({'success': False, 'error': 'Не указан статус'})
        
        # Ищем настраиваемый статус
        from .models import LeadStatus
        try:
            custom_status = LeadStatus.objects.get(slug=status_slug, is_active=True)
        except LeadStatus.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Статус не найден'})
        
        # Удаляем все лиды с этим статусом
        deleted_count = Lead.objects.filter(custom_status=custom_status).delete()[0]
        
        return JsonResponse({
            'success': True,
            'message': f'Удалено {deleted_count} лид(а/ов) из статуса'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Неверные данные запроса'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def convert_lead_to_student(request, pk):
    """Конвертировать лида в студента"""
    from apps.students.models import Student
    from django.contrib import messages
    from django.shortcuts import redirect
    
    try:
        lead = get_object_or_404(Lead, pk=pk)
        
        # Проверяем, не существует ли уже студент с таким телефоном
        existing_student = Student.objects.filter(phone=lead.phone).first()
        if existing_student:
            messages.error(request, f'Студент с телефоном {lead.phone} уже существует!')
            return redirect('leads:detail', pk=lead.pk)
        
        # Создаем студента на основе лида
        student = Student.objects.create(
            full_name=lead.full_name,
            phone=lead.phone,
            source='other',  # Источник "Другое" для сконвертированных лидов
            note=f'Конвертирован из лида. {lead.note or ""}',
            status='active'
        )
        
        # Логируем конвертацию
        from .services import LeadActionLogService
        LeadActionLogService.log_action(
            lead=lead,
            action_type='convert_to_student',
            performed_by=request.user,
            description=f'Лид конвертирован в студента. ID студента: {student.id}',
            request=request
        )
        
        # Архивируем лид после конвертации
        lead.is_archived = True
        lead.save()
        
        messages.success(request, f'Лид "{lead.full_name}" успешно конвертирован в студента!')
        return redirect('students:detail', pk=student.pk)
        
    except Exception as e:
        messages.error(request, f'Ошибка при конвертации лида: {str(e)}')
        return redirect('leads:detail', pk=pk)


@login_required
@require_POST
def lead_delete(request, pk):
    """Удаление одного лида"""
    try:
        lead = get_object_or_404(Lead, pk=pk)
        lead_name = lead.full_name
        
        # Логируем удаление
        from .services import LeadActionLogService
        LeadActionLogService.log_action(
            lead=lead,
            action_type='delete',
            performed_by=request.user,
            description=f'Лид удален пользователем {getattr(request.user, "full_name", "") or request.user.username}',
            request=request
        )
        
        lead.delete()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': f'Лид «{lead_name}» успешно удален'
            })
        else:
            messages.success(request, f'Лид «{lead_name}» успешно удален')
            return redirect('leads:kanban')
            
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': str(e)})
        else:
            messages.error(request, f'Ошибка при удалении лида: {str(e)}')
            return redirect('leads:kanban')


@organization_context
def lead_kanban(request):
    # Импортируем модели только здесь
    from .models import Lead, LeadStatus, LeadSource
    
    # Получаем текущую организацию
    current_org = get_current_organization(request.user)
    lead_queryset = Lead.objects.filter(organization=current_org) if current_org else Lead.objects.none()
    
    # Получаем настраиваемые статусы
    custom_statuses = LeadStatus.objects.filter(is_active=True).order_by('order', 'name')
    
    leads_by_status = {}
    
    if custom_statuses.exists():
        # Используем настраиваемые статусы
        for status in custom_statuses:
            leads_by_status[status.slug] = {
                'label': status.name,
                'color': status.color,
                'status_obj': status,
                'leads': lead_queryset.filter(custom_status=status, is_archived=False)
                           .select_related('interested_course', 'assigned_to', 'custom_status', 'custom_source')
                           .order_by('-created_at'),
            }
        
        # Добавляем лиды без настраиваемого статуса в отдельную колонку
        leads_without_custom_status = lead_queryset.filter(
            custom_status__isnull=True, 
            is_archived=False
        ).select_related('interested_course', 'assigned_to', 'custom_status', 'custom_source').order_by('-created_at')
        
        leads_by_status['without_status'] = {
            'label': 'Без статуса',
            'color': 'bg-secondary',
            'status_obj': None,
            'leads': leads_without_custom_status,
        }
    else:
        # Используем стандартные статусы
        for status, label, color in KANBAN_COLUMNS:
            leads_by_status[status] = {
                'label': label,
                'color': color,
                'status_obj': None,
                'leads': lead_queryset.filter(status=status, is_archived=False)
                           .select_related('interested_course', 'assigned_to', 'custom_status', 'custom_source')
                           .order_by('-created_at'),
            }

    form = SimpleLeadForm()
    context = {
        'leads_by_status': leads_by_status,
        'kanban_columns': KANBAN_COLUMNS,
        'form': form,
        'page_title': 'CRM Лиды',
    }
    return render(request, 'admin/leads/kanban.html', context)


@organization_context
@login_required
def lead_create(request):
    # Получаем текущую организацию
    current_org = get_current_organization(request.user)
    
    if request.method == 'POST':
        form = SimpleLeadForm(request.POST)
        if form.is_valid():
            try:
                # Получаем slug и ищем соответствующий статус
                custom_status_slug = form.cleaned_data.get('custom_status')
                custom_source_slug = form.cleaned_data.get('custom_source')
                
                # Debug информация
                print(f"DEBUG: custom_status_slug = '{custom_status_slug}'")
                print(f"DEBUG: custom_source_slug = '{custom_source_slug}'")
                
                # Ищем настраиваемые статус и источник
                from .models import LeadStatus, LeadSource
                
                if custom_status_slug and custom_status_slug != '':
                    custom_status = LeadStatus.objects.filter(slug=custom_status_slug, is_active=True).first()
                    print(f"DEBUG: найден статус = {custom_status}")
                else:
                    custom_status = None
                    print("DEBUG: статус не выбран")
                    
                if custom_source_slug and custom_source_slug != '':
                    custom_source = LeadSource.objects.filter(slug=custom_source_slug, is_active=True).first()
                    print(f"DEBUG: найден источник = {custom_source}")
                else:
                    custom_source = None
                    print("DEBUG: источник не выбран")
                
                # Получаем ответственное лицо
                assigned_to_id = form.cleaned_data.get('assigned_to')
                assigned_to = None
                if assigned_to_id:
                    try:
                        from django.contrib.auth import get_user_model
                        User = get_user_model()
                        assigned_to = User.objects.filter(pk=assigned_to_id).first()
                    except Exception:
                        assigned_to = None
                
                # Создаем лид с правильными статусами
                lead = Lead.objects.create(
                    full_name=form.cleaned_data['full_name'],
                    phone=form.cleaned_data['phone'],
                    custom_source=custom_source,
                    interested_course=None,  # Временно None
                    assigned_to=assigned_to,
                    custom_status=custom_status,
                    note=form.cleaned_data.get('note', ''),
                    channel='',  # Пустое поле
                    # Явно устанавливаем пустые значения для стандартных полей
                    status='',
                    source='',
                    # Устанавливаем организацию
                    organization=current_org,
                )
                
                print(f"DEBUG: лид создан с custom_status = {lead.custom_status}")
                print(f"DEBUG: лид создан с custom_source = {lead.custom_source}")
                
                # Логируем создание лида
                from .services import LeadActionLogService
                LeadActionLogService.log_action(
                    lead=lead,
                    action_type='create',
                    performed_by=request.user,
                    description=f'Лид создан пользователем {getattr(request.user, "full_name", "") or request.user.username}',
                    request=request
                )
                
                # Логируем назначение менеджера
                if assigned_to:
                    LeadActionLogService.log_assignment(
                        lead=lead,
                        old_manager=None,
                        new_manager=assigned_to,
                        performed_by=request.user,
                        request=request
                    )
                
                # Создаем LeadAction (для обратной совместимости)
                from .models import LeadAction
                status_name = custom_status.name if custom_status else 'Новый'
                # Обрезаем название статуса до 20 символов для LeadAction
                truncated_status_name = status_name[:20] if len(status_name) > 20 else status_name
                LeadAction.objects.create(
                    lead=lead,
                    performed_by=request.user,
                    new_status=truncated_status_name,
                    comment='Лид создан',
                )
                messages.success(request, f'Лид «{lead.full_name}» добавлен.')
                return redirect('leads:kanban')
            except Exception as e:
                messages.error(request, f'Ошибка при создании лида: {str(e)}')
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
    else:
        form = SimpleLeadForm()
    
    return render(request, 'admin/leads/form.html', {'form': form, 'page_title': 'Добавить лид'})

@organization_context
@login_required
def lead_detail(request, pk):
    # Импортируем модели только здесь
    from .models import Lead, LeadAction
    lead = get_object_or_404(Lead, pk=pk)
    actions = lead.actions.select_related('performed_by').all()[:20]
    
    if request.method == 'POST':
        form = SimpleLeadForm(request.POST)
        if form.is_valid():
            # Получаем slug и ищем соответствующий статус
            custom_status_slug = form.cleaned_data.get('custom_status')
            custom_source_slug = form.cleaned_data.get('custom_source')
            
            # Ищем настраиваемые статус и источник
            from .models import LeadStatus, LeadSource
            
            if custom_status_slug and custom_status_slug != '':
                custom_status = LeadStatus.objects.filter(slug=custom_status_slug, is_active=True).first()
            else:
                custom_status = None
                
            if custom_source_slug and custom_source_slug != '':
                custom_source = LeadSource.objects.filter(slug=custom_source_slug, is_active=True).first()
            else:
                custom_source = None
            
            # Получаем ответственное лицо
            assigned_to_id = form.cleaned_data.get('assigned_to')
            assigned_to = None
            if assigned_to_id:
                try:
                    from django.contrib.auth import get_user_model
                    User = get_user_model()
                    assigned_to = User.objects.filter(pk=assigned_to_id).first()
                except Exception:
                    assigned_to = None
            
            # Обновляем лид
            lead.custom_status = custom_status
            lead.custom_source = custom_source
            lead.assigned_to = assigned_to
            lead.note = form.cleaned_data.get('note', '')
            lead.save()
            
            messages.success(request, 'Лид обновлён.')
            return redirect('leads:kanban')
    else:
        # Инициализируем форму с текущими значениями
        initial_data = {
            'full_name': lead.full_name,
            'phone': lead.phone,
            'note': lead.note,
        }
        
        # Добавляем текущие статусы и источники
        if lead.custom_status:
            initial_data['custom_status'] = lead.custom_status.slug
        if lead.custom_source:
            initial_data['custom_source'] = lead.custom_source.slug
        if lead.assigned_to:
            initial_data['assigned_to'] = lead.assigned_to.pk
            
        form = SimpleLeadForm(initial=initial_data)
    
    context = {'lead': lead, 'actions': actions, 'form': form, 'page_title': lead.full_name}
    return render(request, 'admin/leads/detail.html', context)


@require_POST
def lead_move(request, pk):
    """Move lead to a new kanban status via POST."""
    from .models import LeadStatus
    
    lead = get_object_or_404(Lead, pk=pk)
    new_status_slug = request.POST.get('status')
    
    # Проверяем, это настраиваемый статус или стандартный
    try:
        # Сначала ищем среди настраиваемых статусов
        custom_status = LeadStatus.objects.get(slug=new_status_slug, is_active=True)
        old_status_name = lead.custom_status.name if lead.custom_status else lead.get_status_display()
        
        lead.custom_status = custom_status
        lead.status = 'new'  # Устанавливаем стандартный статус для совместимости
        lead.save()
        
        from .models import LeadAction
        LeadAction.objects.create(
            lead=lead,
            performed_by=request.user,
            old_status=old_status_name,
            new_status=custom_status.name,
            comment=f'Перемещён: {old_status_name} → {custom_status.name}',
        )
        return JsonResponse({'status': 'ok', 'new_status': custom_status.name})
        
    except LeadStatus.DoesNotExist:
        # Если не найден среди настраиваемых, проверяем стандартные
        valid_statuses = [s[0] for s in Lead.STATUS_CHOICES]
        if new_status_slug in valid_statuses:
            old_status_name = lead.custom_status.name if lead.custom_status else lead.get_status_display()
            
            lead.status = new_status_slug
            lead.custom_status = None  # Убираем настраиваемый статус
            lead.save()
            
            from .models import LeadAction
            LeadAction.objects.create(
                lead=lead,
                performed_by=request.user,
                old_status=old_status_name,
                new_status=lead.get_status_display(),
                comment=f'Перемещён: {old_status_name} → {lead.get_status_display()}',
            )
            return JsonResponse({'status': 'ok', 'new_status': lead.get_status_display()})
    
    return JsonResponse({'error': 'invalid status'}, status=400)


@login_required
def lead_archive(request):
    leads = Lead.objects.filter(is_archived=True).order_by('-updated_at')
    return render(request, 'admin/leads/archive.html', {'leads': leads, 'page_title': 'Архив лидов'})


# === ФОРМЫ ЛИДОГЕНЕРАЦИИ ===

class LeadFormCreateForm(forms.ModelForm):
    class Meta:
        model = LeadGenerationForm
        fields = ['title', 'channel', 'header', 'description', 'button_text', 
                  'success_text', 'is_active', 'prevent_duplicates', 'auto_create_lead', 'default_status']
        
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            # Явно инициализируем поля для избежания проблем с private_fields
            for field_name in self.fields:
                field = self.fields[field_name]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'channel': forms.Select(attrs={'class': 'form-select'}),
            'header': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'button_text': forms.TextInput(attrs={'class': 'form-control'}),
            'success_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'prevent_duplicates': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'auto_create_lead': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'default_status': forms.Select(attrs={'class': 'form-select'}),
        }


class LeadFormFieldForm(forms.ModelForm):
    class Meta:
        model = LeadFormField
        fields = ['field_name', 'field_type', 'label', 'placeholder', 
                  'is_required', 'order', 'mask', 'options']
        widgets = {
            'field_name': forms.Select(attrs={'class': 'form-select'}),
            'field_type': forms.Select(attrs={'class': 'form-select'}),
            'label': forms.TextInput(attrs={'class': 'form-control'}),
            'placeholder': forms.TextInput(attrs={'class': 'form-control'}),
            'is_required': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
            'mask': forms.TextInput(attrs={'class': 'form-control'}),
            'options': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


@login_required
def form_list(request):
    forms = LeadGenerationForm.objects.all().annotate(
        submissions_count_agg=Count('submissions'),
        leads_count_agg=Count('submissions__leads')
    ).order_by('-created_at')
    
    context = {
        'forms': forms,
        'page_title': 'Формы лидогенерации'
    }
    return render(request, 'admin/leads/forms/list.html', context)


@login_required
def form_create(request):
    if request.method == 'POST':
        form = LeadFormCreateForm(request.POST)
        if form.is_valid():
            lead_form = form.save()
            
            # Создаем поля по умолчанию (только обязательные)
            default_fields = [
                {'field_name': 'first_name', 'label': 'ФИО', 'is_required': True, 'order': 1},
                {'field_name': 'phone', 'label': 'Телефон', 'is_required': True, 'order': 2},
            ]
            
            for field_data in default_fields:
                LeadFormField.objects.create(
                    form=lead_form,
                    field_name=field_data['field_name'],
                    field_type='text' if field_data['field_name'] != 'phone' else 'tel',
                    label=field_data['label'],
                    is_required=field_data['is_required'],
                    order=field_data['order']
                )
            
            messages.success(request, f'Форма «{lead_form.title}» создана с полями по умолчанию.')
            return redirect('leads:form_edit', pk=lead_form.pk)
    else:
        form = LeadFormCreateForm()
    
    context = {
        'form': form,
        'page_title': 'Создать форму'
    }
    return render(request, 'admin/leads/forms/create.html', context)


@login_required
def form_detail(request, pk):
    lead_form = get_object_or_404(LeadGenerationForm, pk=pk)
    fields = lead_form.fields.all().order_by('order')
    submissions = lead_form.submissions.all().order_by('-created_at')[:10]
    
    context = {
        'form': lead_form,
        'fields': fields,
        'submissions': submissions,
        'page_title': f'Форма: {lead_form.title}'
    }
    return render(request, 'admin/leads/forms/detail.html', context)


@login_required
def form_edit(request, pk):
    lead_form = get_object_or_404(LeadGenerationForm, pk=pk)
    fields = lead_form.fields.all().order_by('order')
    
    if request.method == 'POST':
        form = LeadFormCreateForm(request.POST, instance=lead_form)
        if form.is_valid():
            lead_form = form.save()
            messages.success(request, f'Форма «{lead_form.title}» обновлена.')
            return redirect('leads:form_detail', pk=lead_form.pk)
    else:
        form = LeadFormCreateForm(instance=lead_form)
    
    context = {
        'form': form,
        'lead_form': lead_form,
        'fields': fields,
        'page_title': f'Редактировать: {lead_form.title}'
    }
    return render(request, 'admin/leads/forms/edit.html', context)


@login_required
@require_POST
def form_delete(request, pk):
    lead_form = get_object_or_404(LeadGenerationForm, pk=pk)
    title = lead_form.title
    lead_form.delete()
    messages.success(request, f'Форма «{title}» удалена.')
    return redirect('leads:form_list')


@login_required
@require_POST
def form_toggle(request, pk):
    lead_form = get_object_or_404(LeadGenerationForm, pk=pk)
    lead_form.is_active = not lead_form.is_active
    lead_form.save()
    status = 'активирована' if lead_form.is_active else 'деактивирована'
    messages.success(request, f'Форма «{lead_form.title}» {status}.')
    return redirect('leads:form_list')


@login_required
def form_leads(request, pk):
    lead_form = get_object_or_404(LeadGenerationForm, pk=pk)
    leads = Lead.objects.filter(form_submission__form=lead_form).order_by('-created_at')
    
    context = {
        'form': lead_form,
        'leads': leads,
        'page_title': f'Лиды из формы: {lead_form.title}'
    }
    return render(request, 'admin/leads/forms/leads.html', context)


def public_form(request, unique_id):
    lead_form = get_object_or_404(LeadGenerationForm, unique_id=unique_id, is_active=True)
    fields = lead_form.fields.all().order_by('order')
    
    if request.method == 'POST':
        return form_submit(request, unique_id)
    
    context = {
        'form': lead_form,
        'fields': fields,
        'page_title': lead_form.header
    }
    return render(request, 'public/lead_form.html', context)


@csrf_exempt
@require_POST
def form_submit(request, unique_id):
    lead_form = get_object_or_404(LeadGenerationForm, unique_id=unique_id, is_active=True)
    fields = lead_form.fields.all().order_by('order')
    
    # Получаем IP и User Agent
    ip_address = request.META.get('REMOTE_ADDR')
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    # Проверка на дубликаты
    is_duplicate = False
    if lead_form.prevent_duplicates:
        phone = request.POST.get('phone', '')
        email = request.POST.get('email', '')
        
        if phone:
            existing_lead = Lead.objects.filter(phone=phone).first()
            if existing_lead:
                is_duplicate = True
        
        if email and not is_duplicate:
            existing_lead = Lead.objects.filter(
                form_submission__values__field__field_name='email',
                form_submission__values__value=email
            ).first()
            if existing_lead:
                is_duplicate = True
    
    # Создаем отправку формы
    submission = FormSubmission.objects.create(
        form=lead_form,
        ip_address=ip_address,
        user_agent=user_agent,
        is_duplicate=is_duplicate
    )
    
    # Сохраняем значения полей
    for field in fields:
        value = request.POST.get(field.field_name, '')
        if value:
            FormFieldValue.objects.create(
                submission=submission,
                field=field,
                value=value
            )
    
    # Создаем лид если нужно и это не дубликат
    if lead_form.auto_create_lead and not is_duplicate:
        # Собираем данные для лида
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        phone = request.POST.get('phone', '')
        email = request.POST.get('email', '')
        comment = request.POST.get('comment', '')
        
        full_name = f"{first_name} {last_name}".strip()
        if not full_name:
            full_name = request.POST.get('first_name', 'Клиент')
        
        # Создаем лид
        lead = Lead.objects.create(
            full_name=full_name,
            phone=phone,
            source='form',
            channel=lead_form.channel,
            status='new',
            note=f'Из формы: {lead_form.title}\n{comment}',
            form_submission=submission
        )
        
        # Добавляем действие
        LeadAction.objects.create(
            lead=lead,
            performed_by=None, # Автоматическое создание
            new_status='new',
            comment=f'Лид создан из формы "{lead_form.title}"'
        )
    
    return JsonResponse({
        'success': True,
        'message': 'Форма успешно отправлена!',
        'is_duplicate': is_duplicate,
        'redirect_url': f'/form/{unique_id}/success/'
    })


def form_success(request, unique_id):
    """Страница успеха после отправки формы"""
    lead_form = get_object_or_404(LeadGenerationForm, unique_id=unique_id, is_active=True)
    
    context = {
        'form': lead_form,
        'page_title': 'Спасибо!'
    }
    return render(request, 'public/lead_form_success.html', context)


@csrf_exempt
@login_required
@require_POST
def add_field_to_form(request, pk):
    """AJAX view для добавления нового поля в форму"""
    lead_form = get_object_or_404(LeadGenerationForm, pk=pk)
    
    try:
        data = json.loads(request.body)
        
        # Проверяем, что поле с таким именем еще не существует
        if LeadFormField.objects.filter(form=lead_form, field_name=data['field_name']).exists():
            return JsonResponse({'success': False, 'error': 'Поле с таким названием уже существует'})
        
        # Определяем порядок для нового поля
        max_order = LeadFormField.objects.filter(form=lead_form).aggregate(
            Max('order'))['order__max'] or 0
        
        # Создаем новое поле
        field = LeadFormField.objects.create(
            form=lead_form,
            field_name=data['field_name'],
            field_type=data['field_type'],
            label=data['label'],
            placeholder=data.get('placeholder', ''),
            is_required=data.get('is_required', False),
            order=max_order + 1
        )
        
        return JsonResponse({'success': True, 'field_id': field.pk})
        
    except (json.JSONDecodeError, KeyError) as e:
        return JsonResponse({'success': False, 'error': 'Неверные данные запроса'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@csrf_exempt
@login_required
@require_POST
def remove_field_from_form(request, pk):
    """AJAX view для удаления поля из формы"""
    lead_form = get_object_or_404(LeadGenerationForm, pk=pk)
    
    try:
        data = json.loads(request.body)
        field_name = data['field_name']
        
        # Запрещаем удалять обязательные поля
        if field_name in ['first_name', 'phone']:
            return JsonResponse({'success': False, 'error': 'Нельзя удалять обязательные поля'})
        
        # Ищем и удаляем поле
        try:
            field = LeadFormField.objects.get(form=lead_form, field_name=field_name)
            field.delete()
            return JsonResponse({'success': True})
        except LeadFormField.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Поле не найдено'})
        
    except (json.JSONDecodeError, KeyError) as e:
        return JsonResponse({'success': False, 'error': 'Неверные данные запроса'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# ==================== НОВЫЙ ФУНКЦИОНАЛ ====================

@login_required
def lead_duplicates(request):
    """Страница с дубликатами лидов"""
    from .services import LeadDuplicateService
    from .models import LeadDuplicateGroup
    
    # Получаем фильтры
    show_confirmed = request.GET.get('confirmed') == 'true'
    search_query = request.GET.get('search', '')
    
    # Ищем дубликаты
    groups = LeadDuplicateGroup.objects.all()
    
    if show_confirmed:
        groups = groups.filter(is_confirmed=True)
    
    if search_query:
        groups = groups.filter(match_value__icontains=search_query)
    
    # Сортируем по дате создания
    groups = groups.order_by('-created_at').select_related().prefetch_related('duplicates__lead')
    
    context = {
        'groups': groups,
        'show_confirmed': show_confirmed,
        'search_query': search_query,
        'page_title': 'Дубликаты лидов'
    }
    return render(request, 'admin/leads/duplicates.html', context)


@login_required
@require_POST
@login_required
def find_duplicates(request):
    """Запустить поиск дубликатов"""
    from .services import LeadDuplicateService
    from .models import LeadDuplicateGroup
    
    try:
        # Удаляем старые группы дубликатов
        LeadDuplicateGroup.objects.all().delete()
        
        # Ищем новые дубликаты
        groups = LeadDuplicateService.find_duplicates()
        
        messages.success(request, f'Найдено {len(groups)} групп дубликатов')
        
    except Exception as e:
        messages.error(request, f'Ошибка при поиске дубликатов: {str(e)}')
    
    return redirect('leads:duplicates')


@login_required
@require_POST
def merge_leads(request):
    """Объединить дубликаты"""
    from .services import LeadDuplicateService
    from .models import LeadDuplicateGroup
    
    try:
        data = json.loads(request.body)
        primary_lead_id = data.get('primary_lead_id')
        duplicate_lead_ids = data.get('duplicate_lead_ids', [])
        merge_reason = data.get('merge_reason', '')
        
        if not primary_lead_id or not duplicate_lead_ids:
            return JsonResponse({
                'success': False,
                'error': 'Не указаны лиды для объединения'
            })
        
        # Объединяем лиды
        primary_lead = LeadDuplicateService.merge_leads(
            primary_lead_id=primary_lead_id,
            duplicate_lead_ids=duplicate_lead_ids,
            merged_by=request.user,
            merge_reason=merge_reason
        )
        
        # Помечаем группу как обработанную
        group_id = data.get('group_id')
        if group_id:
            LeadDuplicateGroup.objects.filter(id=group_id).update(is_resolved=True)
        
        return JsonResponse({
            'success': True,
            'message': f'Лиды успешно объединены. Основной лид: {primary_lead.full_name}',
            'redirect_url': reverse('leads:detail', kwargs={'pk': primary_lead.id})
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Неверные данные запроса'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_POST
def mark_as_not_duplicate(request):
    """Пометить группу как не дубликат"""
    from .models import LeadDuplicateGroup
    
    try:
        data = json.loads(request.body)
        group_id = data.get('group_id')
        
        if not group_id:
            return JsonResponse({'success': False, 'error': 'Не указана группа'})
        
        group = LeadDuplicateGroup.objects.get(id=group_id)
        group.is_resolved = True
        group.notes = data.get('notes', '')
        group.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Группа помечена как обработанная'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Неверные данные запроса'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def lead_action_logs(request):
    """Страница с историей действий"""
    # Импортируем модели
    from .models import LeadActionLog
    from django.contrib.auth import get_user_model
    from datetime import datetime
    from django.db.models import Q
    User = get_user_model()
    
    # Получаем фильтры
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    action_type = request.GET.get('action_type')
    performed_by_id = request.GET.get('performed_by')
    lead_id = request.GET.get('lead')
    search_query = request.GET.get('search', '')
    
    # Базовый queryset
    logs = LeadActionLog.objects.all()
    
    # Отладочная информация
    total_logs = logs.count()
    print(f"DEBUG: Всего записей в логах: {total_logs}")
    
    # Применяем фильтры
    if start_date and start_date.strip():
        try:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            logs = logs.filter(created_at__date__gte=start_date_obj)
            print(f"DEBUG: Фильтр по начальной дате: {start_date_obj}, осталось: {logs.count()}")
        except ValueError:
            pass  # Неверный формат даты, игнорируем фильтр
    
    if end_date and end_date.strip():
        try:
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
            logs = logs.filter(created_at__date__lte=end_date_obj)
            print(f"DEBUG: Фильтр по конечной дате: {end_date_obj}, осталось: {logs.count()}")
        except ValueError:
            pass  # Неверный формат даты, игнорируем фильтр
    
    if action_type and action_type.strip():
        logs = logs.filter(action_type=action_type)
        print(f"DEBUG: Фильтр по типу действия: {action_type}, осталось: {logs.count()}")
    
    if performed_by_id and performed_by_id.strip():
        logs = logs.filter(performed_by_id=performed_by_id)
        print(f"DEBUG: Фильтр по пользователю: {performed_by_id}, осталось: {logs.count()}")
    
    if lead_id and lead_id.strip():
        logs = logs.filter(lead_id=lead_id)
        print(f"DEBUG: Фильтр по лиду: {lead_id}, осталось: {logs.count()}")
    
    if search_query and search_query.strip():
        logs = logs.filter(
            Q(lead__full_name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(performed_by__username__icontains=search_query)
        )
        print(f"DEBUG: Фильтр по поиску: {search_query}, осталось: {logs.count()}")
    
    print(f"DEBUG: Итоговое количество записей: {logs.count()}")
    
    # Сортировка и пагинация
    logs = logs.order_by('-created_at').select_related('lead', 'performed_by')
    
    # Пагинация
    from django.core.paginator import Paginator
    paginator = Paginator(logs, 50)  # 50 записей на странице
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Получаем данные для фильтров
    action_types = LeadActionLog.ACTION_TYPES
    users = User.objects.filter(lead_action_logs__isnull=False).distinct()
    
    context = {
        'page_obj': page_obj,
        'action_types': action_types,
        'users': users,
        'filters': {
            'start_date': start_date,
            'end_date': end_date,
            'action_type': action_type,
            'performed_by': performed_by_id,
            'lead': lead_id,
            'search': search_query,
        },
        'page_title': 'История действий'
    }
    return render(request, 'admin/leads/action_logs.html', context)


@login_required
def lead_reports(request):
    """Страница с отчетами по лидам"""
    from .services import LeadReportService
    from .models import LeadSource
    from django.contrib.auth import get_user_model
    from datetime import datetime, timedelta
    User = get_user_model()
    
    # Получаем фильтры
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    manager_id = request.GET.get('manager')
    source_id = request.GET.get('source')
    
    # Устанавливаем даты по умолчанию (последние 30 дней)
    if not start_date:
        start_date = (timezone.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    if not end_date:
        end_date = timezone.now().strftime('%Y-%m-%d')
    
    # Конвертируем в даты
    if start_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    if end_date:
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    # Получаем статистику
    stats = LeadReportService.get_lead_statistics(
        start_date=start_date,
        end_date=end_date,
        manager=manager_id,
        source=source_id
    )
    
    # Сериализуем данные для JavaScript
    stats['status_stats_json'] = json.dumps(stats['status_stats'])
    stats['source_stats_json'] = json.dumps(stats['source_stats'])
    
    # Получаем данные для фильтров
    managers = User.objects.filter(assigned_leads__isnull=False).distinct()
    sources = LeadSource.objects.filter(is_active=True)
    
    context = {
        'stats': stats,
        'managers': managers,
        'sources': sources,
        'filters': {
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'manager': manager_id,
            'source': source_id,
        },
        'page_title': 'Отчеты по лидам'
    }
    return render(request, 'admin/leads/reports.html', context)


@login_required
def sales_reports(request):
    """Страница с отчетами по продажам"""
    from .services import LeadReportService
    from django.contrib.auth import get_user_model
    from datetime import datetime, timedelta
    User = get_user_model()
    
    # Получаем фильтры
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    manager_id = request.GET.get('manager')
    course_id = request.GET.get('course')
    
    # Устанавливаем даты по умолчанию (последние 30 дней)
    if not start_date:
        start_date = (timezone.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    if not end_date:
        end_date = timezone.now().strftime('%Y-%m-%d')
    
    # Конвертируем в даты
    if start_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    if end_date:
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    # Получаем статистику продаж
    sales_stats = LeadReportService.get_sales_report(
        start_date=start_date,
        end_date=end_date,
        manager=manager_id,
        course=course_id
    )
    
    # Сериализуем данные для JavaScript
    sales_stats['manager_stats_json'] = json.dumps(sales_stats['manager_stats'])
    sales_stats['course_stats_json'] = json.dumps(sales_stats['course_stats'])
    sales_stats['method_stats_json'] = json.dumps(sales_stats['method_stats'])
    
    # Получаем данные для фильтров
    from apps.courses.models import Course
    from apps.payments.models import Payment
    
    managers = User.objects.filter(created_payments__isnull=False).distinct()
    courses = Course.objects.filter(payments__isnull=False).distinct()
    
    context = {
        'sales_stats': sales_stats,
        'managers': managers,
        'courses': courses,
        'filters': {
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'manager': manager_id,
            'course': course_id,
        },
        'page_title': 'Отчеты по продажам'
    }
    return render(request, 'admin/leads/sales_reports.html', context)


@login_required
def export_leads_report(request):
    """Экспорт отчета по лидам в Excel"""
    import pandas as pd
    from django.http import HttpResponse
    
    from .services import LeadReportService
    from datetime import datetime, timedelta
    
    # Получаем фильтры
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    manager_id = request.GET.get('manager')
    source_id = request.GET.get('source')
    
    if not start_date:
        start_date = (timezone.now() - timedelta(days=30)).date()
    else:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    
    if not end_date:
        end_date = timezone.now().date()
    else:
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    # Получаем данные
    queryset = Lead.objects.filter(
        created_at__date__gte=start_date,
        created_at__date__lte=end_date
    )
    
    if manager_id:
        queryset = queryset.filter(assigned_to_id=manager_id)
    if source_id:
        queryset = queryset.filter(custom_source_id=source_id)
    
    # Формируем DataFrame
    data = []
    for lead in queryset.select_related('assigned_to', 'custom_source', 'interested_course'):
        data.append({
            'ID': lead.id,
            'Имя': lead.full_name,
            'Телефон': lead.phone,
            'Email': lead.email,
            'Статус': lead.current_status,
            'Источник': lead.current_source,
            'Менеджер': getattr(lead.assigned_to, "full_name", "") or (lead.assigned_to.username if lead.assigned_to else ''),
            'Курс': lead.interested_course.title if lead.interested_course else '',
            'Дата создания': lead.created_at.strftime('%d.%m.%Y %H:%M'),
            'Примечание': lead.note,
        })
    
    df = pd.DataFrame(data)
    
    # Создаем Excel файл
    response = HttpResponse(content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = f'attachment; filename=leads_report_{start_date}_{end_date}.xlsx'
    
    df.to_excel(response, index=False, sheet_name='Лиды')
    
    return response


@login_required
def export_sales_report(request):
    """Экспорт отчета по продажам в Excel"""
    import pandas as pd
    from django.http import HttpResponse
    from apps.payments.models import Payment
    from datetime import datetime, timedelta
    
    # Получаем фильтры
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    manager_id = request.GET.get('manager')
    course_id = request.GET.get('course')
    
    if not start_date:
        start_date = (timezone.now() - timedelta(days=30)).date()
    else:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    
    if not end_date:
        end_date = timezone.now().date()
    else:
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    # Получаем данные
    queryset = Payment.objects.filter(
        paid_at__gte=start_date,
        paid_at__lte=end_date
    )
    
    if manager_id:
        queryset = queryset.filter(created_by_id=manager_id)
    if course_id:
        queryset = queryset.filter(course_id=course_id)
    
    # Формируем DataFrame
    data = []
    for payment in queryset.select_related('student', 'course', 'created_by'):
        data.append({
            'ID': payment.id,
            'Студент': payment.student.full_name,
            'Курс': payment.course.title,
            'Сумма': payment.amount,
            'Способ оплаты': payment.get_payment_method_display(),
            'Дата оплаты': payment.paid_at.strftime('%d.%m.%Y'),
            'Кто добавил': getattr(payment.created_by, "full_name", "") or (payment.created_by.username if payment.created_by else ''),
            'Комментарий': payment.comment,
        })
    
    df = pd.DataFrame(data)
    
    # Создаем Excel файл
    response = HttpResponse(content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = f'attachment; filename=sales_report_{start_date}_{end_date}.xlsx'
    
    df.to_excel(response, index=False, sheet_name='Продажи')
    
    return response
