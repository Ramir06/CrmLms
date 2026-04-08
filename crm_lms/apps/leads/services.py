from django.db import transaction
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Q, Count, Avg, Sum, F, Window
from django.db.models.functions import Coalesce, Lower
from difflib import SequenceMatcher
from datetime import datetime, timedelta
import logging

from .models import (
    Lead, LeadDuplicateGroup, LeadDuplicate, LeadMergeHistory, 
    LeadActionLog, LeadReportSnapshot
)

User = get_user_model()
logger = logging.getLogger(__name__)


class LeadDuplicateService:
    """Сервис для работы с дубликатами лидов"""
    
    @staticmethod
    def find_duplicates():
        """Поиск дубликатов лидов"""
        duplicates_found = []
        
        # Поиск по телефону
        phone_duplicates = LeadDuplicateService._find_phone_duplicates()
        duplicates_found.extend(phone_duplicates)
        
        # Поиск по email
        email_duplicates = LeadDuplicateService._find_email_duplicates()
        duplicates_found.extend(email_duplicates)
        
        # Поиск по имени
        name_duplicates = LeadDuplicateService._find_name_duplicates()
        duplicates_found.extend(name_duplicates)
        
        # Поиск по социальным сетям
        social_duplicates = LeadDuplicateService._find_social_duplicates()
        duplicates_found.extend(social_duplicates)
        
        return duplicates_found
    
    @staticmethod
    def _find_phone_duplicates():
        """Поиск дубликатов по телефону"""
        duplicates = []
        phones = Lead.objects.values('phone').annotate(count=Count('id')).filter(count__gt=1)
        
        for phone_data in phones:
            phone = phone_data['phone']
            leads = Lead.objects.filter(phone=phone).order_by('-created_at')
            
            if leads.count() > 1:
                group = LeadDuplicateGroup.objects.create(
                    match_type='phone',
                    match_value=phone,
                    is_confirmed=True  # Телефон - точное совпадение
                )
                
                for i, lead in enumerate(leads):
                    LeadDuplicate.objects.create(
                        group=group,
                        lead=lead,
                        is_primary=(i == 0),  # Первый - основной
                        confidence_score=1.0
                    )
                
                duplicates.append(group)
        
        return duplicates
    
    @staticmethod
    def _find_email_duplicates():
        """Поиск дубликатов по email"""
        duplicates = []
        emails = Lead.objects.exclude(email='').values('email').annotate(count=Count('id')).filter(count__gt=1)
        
        for email_data in emails:
            email = email_data['email']
            leads = Lead.objects.filter(email=email).order_by('-created_at')
            
            if leads.count() > 1:
                group = LeadDuplicateGroup.objects.create(
                    match_type='email',
                    match_value=email,
                    is_confirmed=True  # Email - точное совпадение
                )
                
                for i, lead in enumerate(leads):
                    LeadDuplicate.objects.create(
                        group=group,
                        lead=lead,
                        is_primary=(i == 0),
                        confidence_score=1.0
                    )
                
                duplicates.append(group)
        
        return duplicates
    
    @staticmethod
    def _find_name_duplicates():
        """Поиск дубликатов по похожим именам"""
        duplicates = []
        leads = Lead.objects.all().order_by('full_name')
        
        # Группировка по похожим именам
        name_groups = {}
        for lead in leads:
            lead_name = lead.full_name.lower().strip()
            found_group = False
            
            for group_name in name_groups:
                similarity = SequenceMatcher(None, lead_name, group_name).ratio()
                if similarity > 0.8:  # 80% схожести
                    name_groups[group_name].append((lead, similarity))
                    found_group = True
                    break
            
            if not found_group:
                name_groups[lead_name] = [(lead, 1.0)]
        
        # Создаем группы для найденных дубликатов
        for group_name, lead_list in name_groups.items():
            if len(lead_list) > 1:
                group = LeadDuplicateGroup.objects.create(
                    match_type='full_name',
                    match_value=group_name,
                    is_confirmed=False  # Имена - неточное совпадение
                )
                
                # Сортируем по уверенности
                lead_list.sort(key=lambda x: x[1], reverse=True)
                
                for i, (lead, confidence) in enumerate(lead_list):
                    LeadDuplicate.objects.create(
                        group=group,
                        lead=lead,
                        is_primary=(i == 0),
                        confidence_score=confidence
                    )
                
                duplicates.append(group)
        
        return duplicates
    
    @staticmethod
    def _find_social_duplicates():
        """Поиск дубликатов по социальным сетям"""
        duplicates = []
        
        # Telegram
        telegram_duplicates = LeadDuplicateService._find_social_field_duplicates('telegram')
        duplicates.extend(telegram_duplicates)
        
        # Instagram
        instagram_duplicates = LeadDuplicateService._find_social_field_duplicates('instagram')
        duplicates.extend(instagram_duplicates)
        
        # WhatsApp
        whatsapp_duplicates = LeadDuplicateService._find_social_field_duplicates('whatsapp')
        duplicates.extend(whatsapp_duplicates)
        
        # Username
        username_duplicates = LeadDuplicateService._find_social_field_duplicates('username')
        duplicates.extend(username_duplicates)
        
        return duplicates
    
    @staticmethod
    def _find_social_field_duplicates(field_name):
        """Поиск дубликатов по конкретному полю социальной сети"""
        duplicates = []
        filter_kwargs = {f'{field_name}__isnull': False, f'{field_name}__ne': ''}
        
        # Используем Q для сложных условий
        query = Q(**{f'{field_name}__isnull': False}) & ~Q(**{f'{field_name}': ''})
        
        values = Lead.objects.filter(query).values(field_name).annotate(count=Count('id')).filter(count__gt=1)
        
        for value_data in values:
            value = value_data[field_name]
            leads = Lead.objects.filter(**{field_name: value}).order_by('-created_at')
            
            if leads.count() > 1:
                group = LeadDuplicateGroup.objects.create(
                    match_type=field_name,
                    match_value=value,
                    is_confirmed=True
                )
                
                for i, lead in enumerate(leads):
                    LeadDuplicate.objects.create(
                        group=group,
                        lead=lead,
                        is_primary=(i == 0),
                        confidence_score=1.0
                    )
                
                duplicates.append(group)
        
        return duplicates
    
    @staticmethod
    def merge_leads(primary_lead_id, duplicate_lead_ids, merged_by, merge_reason=""):
        """Объединение дубликатов"""
        with transaction.atomic():
            primary_lead = Lead.objects.get(id=primary_lead_id)
            duplicate_leads = Lead.objects.filter(id__in=duplicate_lead_ids)
            
            fields_merged = {}
            
            for duplicate_lead in duplicate_leads:
                # Собираем информацию о том, какие поля были объединены
                for field in Lead._meta.fields:
                    field_name = field.name
                    if field_name in ['id', 'created_at', 'updated_at']:
                        continue
                    
                    primary_value = getattr(primary_lead, field_name)
                    duplicate_value = getattr(duplicate_lead, field_name)
                    
                    # Если в основном лиде пусто, а в дубликате есть данные
                    if not primary_value and duplicate_value:
                        setattr(primary_lead, field_name, duplicate_value)
                        fields_merged[f'{field_name}_from_lead_{duplicate_lead.id}'] = str(duplicate_value)
                
                # Записываем историю объединения
                LeadMergeHistory.objects.create(
                    primary_lead=primary_lead,
                    merged_lead=duplicate_lead,
                    merged_by=merged_by,
                    merge_reason=merge_reason,
                    fields_merged=fields_merged
                )
                
                # Логируем объединение
                LeadActionLogService.log_action(
                    lead=duplicate_lead,
                    action_type='merge',
                    performed_by=merged_by,
                    description=f'Лид объединен с {primary_lead.full_name}. Причина: {merge_reason}'
                )
                
                # Архивируем дубликат (не удаляем!)
                duplicate_lead.is_archived = True
                duplicate_lead.save()
            
            primary_lead.save()
            
            # Логируем для основного лида
            LeadActionLogService.log_action(
                lead=primary_lead,
                action_type='merge',
                performed_by=merged_by,
                description=f'Объединено с лидами: {", ".join([str(l) for l in duplicate_leads])}'
            )
            
            return primary_lead


class LeadActionLogService:
    """Сервис для логирования действий с лидами"""
    
    @staticmethod
    def log_action(lead, action_type, performed_by=None, old_value="", new_value="", 
                   field_name="", description="", request=None):
        """Записать действие в лог"""
        ip_address = None
        user_agent = ""
        
        if request:
            ip_address = LeadActionLogService._get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        LeadActionLog.objects.create(
            lead=lead,
            action_type=action_type,
            performed_by=performed_by,
            old_value=old_value,
            new_value=new_value,
            field_name=field_name,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    @staticmethod
    def _get_client_ip(request):
        """Получить IP адрес клиента"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    @staticmethod
    def log_field_change(lead, field_name, old_value, new_value, performed_by=None, request=None):
        """Логировать изменение поля"""
        LeadActionLogService.log_action(
            lead=lead,
            action_type='update',
            performed_by=performed_by,
            old_value=str(old_value),
            new_value=str(new_value),
            field_name=field_name,
            description=f'Изменено поле "{field_name}"',
            request=request
        )
    
    @staticmethod
    def log_status_change(lead, old_status, new_status, performed_by=None, request=None):
        """Логировать смену статуса"""
        LeadActionLogService.log_action(
            lead=lead,
            action_type='status_change',
            performed_by=performed_by,
            old_value=str(old_status),
            new_value=str(new_status),
            field_name='status',
            description=f'Статус изменен с "{old_status}" на "{new_status}"',
            request=request
        )
    
    @staticmethod
    def log_assignment(lead, old_manager, new_manager, performed_by=None, request=None):
        """Логировать назначение менеджера"""
        old_name = str(old_manager) if old_manager else "Не назначен"
        new_name = str(new_manager) if new_manager else "Не назначен"
        
        LeadActionLogService.log_action(
            lead=lead,
            action_type='assign',
            performed_by=performed_by,
            old_value=old_name,
            new_value=new_name,
            field_name='assigned_to',
            description=f'Назначен менеджер: {new_name}',
            request=request
        )


class LeadReportService:
    """Сервис для генерации отчетов по лидам"""
    
    @staticmethod
    def get_lead_statistics(start_date=None, end_date=None, manager=None, source=None):
        """Получить статистику по лидам"""
        queryset = Lead.objects.all()
        
        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)
        if manager:
            queryset = queryset.filter(assigned_to=manager)
        if source:
            queryset = queryset.filter(custom_source=source)
        
        # Общая статистика
        total_leads = queryset.count()
        new_leads = queryset.filter(status='new').count()
        archived_leads = queryset.filter(is_archived=True).count()
        
        # По статусам
        status_stats = queryset.values('status').annotate(count=Count('id'))
        
        # По источникам
        source_stats = queryset.values('source').annotate(count=Count('id'))
        
        # По менеджерам
        manager_stats = queryset.values('assigned_to__username').annotate(count=Count('id'))
        
        # Конверсии
        converted_leads = queryset.filter(status='enrolling').count()
        conversion_rate = (converted_leads / total_leads * 100) if total_leads > 0 else 0
        
        # Среднее время обработки
        avg_processing_time = LeadReportService._calculate_avg_processing_time(queryset)
        
        return {
            'total_leads': total_leads,
            'new_leads': new_leads,
            'archived_leads': archived_leads,
            'converted_leads': converted_leads,
            'conversion_rate': round(conversion_rate, 2),
            'avg_processing_time': round(avg_processing_time, 2),
            'status_stats': list(status_stats),
            'source_stats': list(source_stats),
            'manager_stats': list(manager_stats),
        }
    
    @staticmethod
    def _calculate_avg_processing_time(queryset):
        """Рассчитать среднее время обработки лида"""
        # Время от создания до первого изменения статуса
        # Это упрощенный расчет - в реальном проекте нужно более сложное определение
        leads_with_actions = queryset.filter(actions__isnull=False).distinct()
        
        if not leads_with_actions.exists():
            return 0
        
        total_time = 0
        count = 0
        
        for lead in leads_with_actions:
            first_action = lead.actions.order_by('created_at').first()
            if first_action:
                time_diff = first_action.created_at - lead.created_at
                total_time += time_diff.total_seconds() / 3600  # в часах
                count += 1
        
        return total_time / count if count > 0 else 0
    
    @staticmethod
    def get_sales_report(start_date=None, end_date=None, manager=None, course=None):
        """Получить отчет по продажам"""
        # Импортируем здесь чтобы избежать циклического импорта
        from apps.payments.models import Payment
        from apps.students.models import Student
        
        queryset = Payment.objects.all()
        
        if start_date:
            queryset = queryset.filter(paid_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(paid_at__lte=end_date)
        if manager:
            queryset = queryset.filter(created_by=manager)
        if course:
            queryset = queryset.filter(course=course)
        
        # Общая статистика
        total_payments = queryset.count()
        total_amount = queryset.aggregate(total=Sum('amount'))['total'] or 0
        avg_payment = total_amount / total_payments if total_payments > 0 else 0
        
        # По менеджерам
        manager_stats = (
            queryset.values('created_by__username')
            .annotate(count=Count('id'), amount=Sum('amount'))
            .order_by('-amount')
        )
        
        # По курсам
        course_stats = (
            queryset.values('course__title')
            .annotate(count=Count('id'), amount=Sum('amount'))
            .order_by('-amount')
        )
        
        # По способам оплаты
        method_stats = (
            queryset.values('payment_method')
            .annotate(count=Count('id'), amount=Sum('amount'))
        )
        
        # Конверсия из лидов в продажи
        leads_converted = Student.objects.filter(
            created_at__gte=start_date or timezone.now() - timedelta(days=30)
        ).count()
        
        conversion_rate = (total_payments / leads_converted * 100) if leads_converted > 0 else 0
        
        return {
            'total_payments': total_payments,
            'total_amount': total_amount,
            'avg_payment': round(avg_payment, 2),
            'conversion_rate': round(conversion_rate, 2),
            'manager_stats': list(manager_stats),
            'course_stats': list(course_stats),
            'method_stats': list(method_stats),
        }
    
    @staticmethod
    def create_daily_snapshot():
        """Создать ежедневный снепшот для отчетов"""
        today = timezone.now().date()
        
        # Проверяем, не существует ли уже снепшот за сегодня
        if LeadReportSnapshot.objects.filter(report_date=today).exists():
            return
        
        stats = LeadReportService.get_lead_statistics()
        
        LeadReportSnapshot.objects.create(
            report_date=today,
            total_leads=stats['total_leads'],
            new_leads=stats['new_leads'],
            converted_leads=stats['converted_leads'],
            lost_leads=stats['archived_leads'],
            conversion_rate=stats['conversion_rate'],
            avg_processing_time=stats['avg_processing_time']
        )


class LeadValidationService:
    """Сервис для валидации лидов"""
    
    @staticmethod
    def check_for_duplicates_on_create(lead_data):
        """Проверить дубликаты при создании лида"""
        potential_duplicates = []
        
        # Проверка по телефону
        if lead_data.get('phone'):
            phone_leads = Lead.objects.filter(phone=lead_data['phone'])
            if phone_leads.exists():
                potential_duplicates.extend(phone_leads)
        
        # Проверка по email
        if lead_data.get('email'):
            email_leads = Lead.objects.filter(email=lead_data['email'])
            if email_leads.exists():
                potential_duplicates.extend(email_leads)
        
        # Проверка по имени
        if lead_data.get('full_name'):
            similar_leads = Lead.objects.filter(
                full_name__icontains=lead_data['full_name'].split()[0]
            )
            if similar_leads.exists():
                potential_duplicates.extend(similar_leads)
        
        return list(set(potential_duplicates))  # Убираем дубликаты из списка
