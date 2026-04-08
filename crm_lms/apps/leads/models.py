from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid
from apps.core.models import TimeStampedModel, OrganizationMixin


class LeadStatus(TimeStampedModel):
    """Настраиваемые статусы лидов"""
    name = models.CharField(max_length=50, unique=True, verbose_name='Название статуса')
    slug = models.SlugField(max_length=50, unique=True, verbose_name='Slug')
    description = models.TextField(blank=True, verbose_name='Описание')
    color = models.CharField(max_length=7, default='#007bff', verbose_name='Цвет')
    icon = models.ImageField(upload_to='lead_status_icons/', blank=True, null=True, verbose_name='Иконка')
    is_default = models.BooleanField(default=False, verbose_name='Статус по умолчанию')
    is_active = models.BooleanField(default=True, verbose_name='Активен')
    order = models.PositiveIntegerField(default=0, verbose_name='Порядок сортировки')
    
    class Meta:
        verbose_name = 'Статус лида'
        verbose_name_plural = 'Статусы лидов'
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        # Только один статус может быть по умолчанию
        if self.is_default:
            LeadStatus.objects.filter(is_default=True).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)


class LeadSource(TimeStampedModel):
    """Настраиваемые источники лидов"""
    name = models.CharField(max_length=50, unique=True, verbose_name='Название источника')
    slug = models.SlugField(max_length=50, unique=True, verbose_name='Slug')
    description = models.TextField(blank=True, verbose_name='Описание')
    icon = models.ImageField(upload_to='lead_source_icons/', blank=True, null=True, verbose_name='Иконка')
    is_default = models.BooleanField(default=False, verbose_name='Источник по умолчанию')
    is_active = models.BooleanField(default=True, verbose_name='Активен')
    order = models.PositiveIntegerField(default=0, verbose_name='Порядок сортировки')
    
    class Meta:
        verbose_name = 'Источник лида'
        verbose_name_plural = 'Источники лидов'
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        # Только один источник может быть по умолчанию
        if self.is_default:
            LeadSource.objects.filter(is_default=True).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)


class Lead(OrganizationMixin, TimeStampedModel):
    # Старые варианты для совместимости
    STATUS_CHOICES = [
        ('new', 'Новый'),
        ('consultation', 'Консультация'),
        ('trial_lesson', 'Пробный урок'),
        ('no_show', 'Не пришёл'),
        ('enrolling', 'Зачисление'),
        ('rejected', 'Отказ'),
    ]
    SOURCE_CHOICES = [
        ('instagram', 'Instagram'),
        ('telegram', 'Telegram'),
        ('referral', 'Реферал'),
        ('website', 'Сайт'),
        ('vk', 'ВКонтакте'),
        ('other', 'Другое'),
        ('form', 'Форма'),
    ]

    full_name = models.CharField(max_length=200, verbose_name='Полное имя')
    phone = models.CharField(max_length=20, verbose_name='Телефон')
    email = models.EmailField(blank=True, verbose_name='Email')
    
    # Социальные сети
    telegram = models.CharField(max_length=100, blank=True, verbose_name='Telegram')
    instagram = models.CharField(max_length=100, blank=True, verbose_name='Instagram')
    whatsapp = models.CharField(max_length=20, blank=True, verbose_name='WhatsApp')
    username = models.CharField(max_length=100, blank=True, verbose_name='Username')
    
    # Новые поля для настраиваемых статусов и источников
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='new', 
        verbose_name='Статус (старый вариант)'
    )
    custom_status = models.ForeignKey(
        'LeadStatus', on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name='Статус'
    )
    
    source = models.CharField(
        max_length=20, choices=SOURCE_CHOICES, blank=True, 
        verbose_name='Источник (старый вариант)'
    )
    custom_source = models.ForeignKey(
        'LeadSource', on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name='Источник'
    )
    
    interested_course = models.ForeignKey(
        'courses.Course', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='leads', verbose_name='Интересующий курс'
    )
    channel = models.CharField(max_length=100, blank=True, verbose_name='Канал')
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='assigned_leads', verbose_name='Ответственный'
    )
    note = models.TextField(blank=True, verbose_name='Примечание')
    is_archived = models.BooleanField(default=False, verbose_name='В архиве')
    form_submission = models.ForeignKey('FormSubmission', on_delete=models.SET_NULL, null=True, blank=True, 
                                     related_name='leads', verbose_name='Отправка формы')

    class Meta:
        verbose_name = 'Лид'
        verbose_name_plural = 'Лиды'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.full_name} ({self.phone})'
    
    @property
    def current_status(self):
        """Возвращает текущий статус (предпочитая custom_status)"""
        if self.custom_status:
            return self.custom_status
        return self.get_status_display()
    
    @property
    def current_source(self):
        """Возвращает текущий источник (предпочитая custom_source)"""
        if self.custom_source:
            return self.custom_source
        return self.get_source_display()


class LeadGenerationForm(models.Model):
    """Форма лидогенерации"""
    CHANNEL_CHOICES = [
        ('facebook', 'Facebook'),
        ('instagram', 'Instagram'),
        ('telegram', 'Telegram'),
        ('website', 'Website'),
        ('other', 'Другое'),
    ]
    
    title = models.CharField('Название формы', max_length=200)
    channel = models.CharField('Канал', max_length=20, choices=CHANNEL_CHOICES)
    header = models.CharField('Заголовок формы', max_length=300)
    description = models.TextField('Описание', blank=True)
    button_text = models.CharField('Текст кнопки', max_length=100, default='Отправить')
    success_text = models.TextField('Текст после отправки', default='Спасибо за заявку!')
    is_active = models.BooleanField('Активна', default=True)
    prevent_duplicates = models.BooleanField('Защита от дублей', default=True)
    auto_create_lead = models.BooleanField('Автосоздание лида', default=True)
    default_status = models.ForeignKey(
        'LeadStatus', on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name='Статус лида по умолчанию',
        help_text='Статус, который будет присвоен лидам из этой формы'
    )
    unique_id = models.UUIDField('Уникальный ID', unique=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField('Создана', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлена', auto_now=True)
    
    class Meta:
        verbose_name = 'Форма лидогенерации'
        verbose_name_plural = 'Формы лидогенерации'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return f'/form/{self.unique_id}/'
    
    @property
    def submissions_count(self):
        return self.submissions.count()
    
    @property
    def leads_count(self):
        return self.submissions.filter(leads__isnull=False).count()
    
    @property
    def conversion_rate(self):
        total = self.submissions_count
        if total == 0:
            return 0
        return (self.leads_count / total) * 100


class LeadFormField(TimeStampedModel):
    FIELD_TYPES = [
        ('text', 'Текст'),
        ('tel', 'Телефон'),
        ('email', 'Email'),
        ('number', 'Число'),
        ('date', 'Дата'),
        ('textarea', 'Текстовая область'),
        ('select', 'Выбор'),
    ]
    
    FIELD_NAMES = [
        ('first_name', 'Имя'),
        ('last_name', 'Фамилия'),
        ('phone', 'Телефон'),
        ('whatsapp', 'WhatsApp'),
        ('telegram', 'Telegram'),
        ('email', 'Email'),
        ('age', 'Возраст'),
        ('city', 'Город'),
        ('course', 'Курс/направление'),
        ('comment', 'Комментарий'),
        ('birth_date', 'Дата рождения'),
    ]
    
    form = models.ForeignKey(LeadGenerationForm, on_delete=models.CASCADE, related_name='fields', verbose_name='Форма')
    field_name = models.CharField(max_length=20, choices=FIELD_NAMES, verbose_name='Название поля')
    field_type = models.CharField(max_length=20, choices=FIELD_TYPES, default='text', verbose_name='Тип поля')
    label = models.CharField(max_length=100, verbose_name='Label поля')
    placeholder = models.CharField(max_length=200, blank=True, verbose_name='Placeholder')
    is_required = models.BooleanField(default=False, verbose_name='Обязательное поле')
    order = models.PositiveIntegerField(default=0, verbose_name='Порядок')
    mask = models.CharField(max_length=50, blank=True, verbose_name='Маска')
    options = models.TextField(blank=True, help_text='Опции для select поля (каждая с новой строки)', verbose_name='Опции')
    
    class Meta:
        verbose_name = 'Поле формы'
        verbose_name_plural = 'Поля формы'
        ordering = ['order']

    def __str__(self):
        return f'{self.form.title} - {self.label}'


class FormSubmission(TimeStampedModel):
    form = models.ForeignKey(LeadGenerationForm, on_delete=models.CASCADE, related_name='submissions', verbose_name='Форма')
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name='IP адрес')
    user_agent = models.TextField(blank=True, verbose_name='User Agent')
    is_duplicate = models.BooleanField(default=False, verbose_name='Дубликат')
    
    class Meta:
        verbose_name = 'Отправка формы'
        verbose_name_plural = 'Отправки форм'
        ordering = ['-created_at']

    def __str__(self):
        return f'Отправка формы {self.form.title} от {self.created_at.strftime("%d.%m.%Y %H:%M")}'


class FormFieldValue(TimeStampedModel):
    submission = models.ForeignKey(FormSubmission, on_delete=models.CASCADE, related_name='values', verbose_name='Отправка')
    field = models.ForeignKey(LeadFormField, on_delete=models.CASCADE, verbose_name='Поле')
    value = models.TextField(verbose_name='Значение')
    
    class Meta:
        verbose_name = 'Значение поля формы'
        verbose_name_plural = 'Значения полей формы'
        unique_together = ['submission', 'field']

    def __str__(self):
        return f'{self.field.label}: {self.value}'


class LeadAction(models.Model):
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='actions', verbose_name='Лид')
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        verbose_name='Кто выполнил'
    )
    old_status = models.CharField(max_length=20, blank=True)
    new_status = models.CharField(max_length=20, blank=True)
    comment = models.TextField(blank=True, verbose_name='Комментарий')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Действие с лидом'
        verbose_name_plural = 'Действия с лидами'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.lead} → {self.new_status}'


class LeadDuplicateGroup(TimeStampedModel):
    """Группа дубликатов лидов"""
    MATCH_TYPE_CHOICES = [
        ('phone', 'Телефон'),
        ('email', 'Email'),
        ('name', 'Имя'),
        ('full_name', 'Полное имя'),
        ('telegram', 'Telegram'),
        ('instagram', 'Instagram'),
        ('whatsapp', 'WhatsApp'),
    ]
    
    match_type = models.CharField(
        max_length=20, choices=MATCH_TYPE_CHOICES,
        verbose_name='Тип совпадения'
    )
    match_value = models.CharField(
        max_length=255, verbose_name='Значение совпадения'
    )
    is_confirmed = models.BooleanField(
        default=False, verbose_name='Подтвержденные дубли'
    )
    is_resolved = models.BooleanField(
        default=False, verbose_name='Обработано'
    )
    notes = models.TextField(
        blank=True, verbose_name='Заметки'
    )

    class Meta:
        verbose_name = 'Группа дубликатов'
        verbose_name_plural = 'Группы дубликатов'
        ordering = ['-created_at']

    def __str__(self):
        return f'Дубли по {self.get_match_type_display()}: {self.match_value}'


class LeadDuplicate(models.Model):
    """Запись о дубликате лида"""
    group = models.ForeignKey(
        LeadDuplicateGroup, on_delete=models.CASCADE,
        related_name='duplicates', verbose_name='Группа'
    )
    lead = models.ForeignKey(
        Lead, on_delete=models.CASCADE,
        related_name='duplicate_records', verbose_name='Лид'
    )
    is_primary = models.BooleanField(
        default=False, verbose_name='Основной лид'
    )
    confidence_score = models.FloatField(
        default=0.0, verbose_name='Уверенность в дубликате'
    )

    class Meta:
        verbose_name = 'Дубликат лида'
        verbose_name_plural = 'Дубликаты лидов'
        unique_together = ['group', 'lead']
        ordering = ['-confidence_score']

    def __str__(self):
        return f'{self.lead} (группа {self.group.id})'


class LeadMergeHistory(TimeStampedModel):
    """История объединения лидов"""
    primary_lead = models.ForeignKey(
        Lead, on_delete=models.CASCADE,
        related_name='merge_primary', verbose_name='Основной лид'
    )
    merged_lead = models.ForeignKey(
        Lead, on_delete=models.CASCADE,
        related_name='merge_merged', verbose_name='Объединенный лид'
    )
    merged_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        verbose_name='Кто объединил'
    )
    merge_reason = models.TextField(
        verbose_name='Причина объединения'
    )
    fields_merged = models.JSONField(
        default=dict, verbose_name='Объединенные поля'
    )

    class Meta:
        verbose_name = 'История объединения'
        verbose_name_plural = 'Истории объединений'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.merged_lead} → {self.primary_lead}'


class LeadActionLog(TimeStampedModel):
    """Подробный лог действий с лидами (audit log)"""
    ACTION_TYPES = [
        ('create', 'Создание'),
        ('update', 'Редактирование'),
        ('status_change', 'Смена статуса'),
        ('assign', 'Назначение менеджера'),
        ('comment', 'Добавление комментария'),
        ('merge', 'Объединение'),
        ('archive', 'Архивирование'),
        ('delete', 'Удаление'),
        ('convert_to_student', 'Конвертация в студента'),
        ('import', 'Импорт'),
    ]
    
    lead = models.ForeignKey(
        Lead, on_delete=models.CASCADE,
        related_name='action_logs', verbose_name='Лид'
    )
    action_type = models.CharField(
        max_length=20, choices=ACTION_TYPES,
        verbose_name='Тип действия'
    )
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='lead_action_logs', verbose_name='Кто выполнил'
    )
    old_value = models.TextField(
        blank=True, verbose_name='Старое значение'
    )
    new_value = models.TextField(
        blank=True, verbose_name='Новое значение'
    )
    field_name = models.CharField(
        max_length=50, blank=True, verbose_name='Название поля'
    )
    description = models.TextField(
        blank=True, verbose_name='Описание'
    )
    ip_address = models.GenericIPAddressField(
        null=True, blank=True, verbose_name='IP адрес'
    )
    user_agent = models.TextField(
        blank=True, verbose_name='User Agent'
    )

    class Meta:
        verbose_name = 'Лог действия'
        verbose_name_plural = 'Логи действий'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['lead', '-created_at']),
            models.Index(fields=['performed_by', '-created_at']),
            models.Index(fields=['action_type', '-created_at']),
        ]

    def __str__(self):
        return f'{self.get_action_type_display()}: {self.lead}'


class LeadReportSnapshot(TimeStampedModel):
    """Снепшот данных для отчетов"""
    report_date = models.DateField(
        verbose_name='Дата отчета'
    )
    total_leads = models.IntegerField(
        default=0, verbose_name='Всего лидов'
    )
    new_leads = models.IntegerField(
        default=0, verbose_name='Новых лидов'
    )
    converted_leads = models.IntegerField(
        default=0, verbose_name='Конвертировано'
    )
    lost_leads = models.IntegerField(
        default=0, verbose_name='Потеряно'
    )
    conversion_rate = models.FloatField(
        default=0.0, verbose_name='Конверсия %'
    )
    avg_processing_time = models.FloatField(
        default=0.0, verbose_name='Среднее время обработки (часы)'
    )

    class Meta:
        verbose_name = 'Снепшот отчета'
        verbose_name_plural = 'Снепшоты отчетов'
        ordering = ['-report_date']
        unique_together = ['report_date']

    def __str__(self):
        return f'Отчет за {self.report_date}'
