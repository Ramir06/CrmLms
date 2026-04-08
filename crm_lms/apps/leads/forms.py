from django import forms
from .models import LeadStatus, LeadSource


class SimpleLeadForm(forms.Form):
    def __init__(self, *args, **kwargs):
        # Убираем instance из kwargs если он есть
        kwargs.pop('instance', None)
        super().__init__(*args, **kwargs)
        
        # Простые поля без моделей
        self.fields['full_name'] = forms.CharField(max_length=200, label='ФИО', widget=forms.TextInput(attrs={'class': 'form-control'}))
        self.fields['phone'] = forms.CharField(max_length=20, label='Номер телефона', widget=forms.TextInput(attrs={'class': 'form-control'}))
        self.fields['note'] = forms.CharField(required=False, label='Примечание', widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}))
        
        # Настраиваемые статусы из базы данных
        status_choices = [('', 'Выберите статус')] + [(status.slug, status.name) for status in LeadStatus.objects.filter(is_active=True).order_by('order', 'name')]
        if len(status_choices) == 1:  # Только пустой вариант
            # Если нет настраиваемых, используем стандартные
            status_choices = [('', 'Выберите статус'), ('new', 'Новый'), ('consultation', 'Консультация'), ('trial_lesson', 'Пробный урок'), ('no_show', 'Не пришёл'), ('enrolling', 'Зачисление'), ('rejected', 'Отказ')]
        
        self.fields['custom_status'] = forms.ChoiceField(label='Статус', choices=status_choices, required=False, widget=forms.Select(attrs={'class': 'form-select'}))
        
        # Настраиваемые источники из базы данных
        source_choices = [('', 'Выберите источник')] + [(source.slug, source.name) for source in LeadSource.objects.filter(is_active=True).order_by('order', 'name')]
        if len(source_choices) == 1:  # Только пустой вариант
            # Если нет настраиваемых, используем стандартные
            source_choices = [('', 'Выберите источник'), ('website', 'Сайт'), ('instagram', 'Instagram'), ('telegram', 'Telegram'), ('vk', 'ВКонтакте'), ('referral', 'Реферал'), ('form', 'Форма'), ('other', 'Другое')]
        
        self.fields['custom_source'] = forms.ChoiceField(label='Источник', choices=source_choices, required=False, widget=forms.Select(attrs={'class': 'form-select'}))
        
        # Интересующее направление
        self.fields['interested_course'] = forms.CharField(required=False, label='Интересующее направление', widget=forms.TextInput(attrs={'class': 'form-control'}))
        
        # Ответственное лицо - только администраторы
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            admin_users = User.objects.filter(role='admin', is_active=True).order_by('first_name', 'last_name')
            admin_choices = [(user.pk, str(user)) for user in admin_users]
            if admin_choices:
                self.fields['assigned_to'] = forms.ChoiceField(required=False, label='Ответственное лицо', choices=[('', '----------')] + admin_choices, widget=forms.Select(attrs={'class': 'form-select'}))
            else:
                self.fields['assigned_to'] = forms.CharField(required=False, label='Ответственное лицо', widget=forms.TextInput(attrs={'class': 'form-control'}))
        except Exception:
            # Если ошибка с CustomUser, используем простое поле
            self.fields['assigned_to'] = forms.CharField(required=False, label='Ответственное лицо', widget=forms.TextInput(attrs={'class': 'form-control'}))
        
        # Устанавливаем начальные значения
        if 'custom_status' not in self.initial:
            default_status = LeadStatus.objects.filter(is_default=True).first()
            if default_status:
                self.initial['custom_status'] = default_status.slug
        
        if 'custom_source' not in self.initial:
            default_source = LeadSource.objects.filter(is_default=True).first()
            if default_source:
                self.initial['custom_source'] = default_source.slug


class LeadStatusForm(forms.ModelForm):
    class Meta:
        model = LeadStatus
        fields = ['name', 'slug', 'description', 'color', 'icon', 'is_default', 'is_active', 'order']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'slug': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'color': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
            'icon': forms.FileInput(attrs={'class': 'form-control'}),
            'is_default': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].label = 'Название статуса'
        self.fields['slug'].label = 'Slug'
        self.fields['description'].label = 'Описание'
        self.fields['color'].label = 'Цвет'
        self.fields['icon'].label = 'Иконка'
        self.fields['is_default'].label = 'Статус по умолчанию'
        self.fields['is_active'].label = 'Активен'
        self.fields['order'].label = 'Порядок сортировки'


class LeadSourceForm(forms.ModelForm):
    class Meta:
        model = LeadSource
        fields = ['name', 'slug', 'description', 'icon', 'is_default', 'is_active', 'order']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'slug': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'icon': forms.FileInput(attrs={'class': 'form-control'}),
            'is_default': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].label = 'Название источника'
        self.fields['slug'].label = 'Slug'
        self.fields['description'].label = 'Описание'
        self.fields['icon'].label = 'Иконка'
        self.fields['is_default'].label = 'Источник по умолчанию'
        self.fields['is_active'].label = 'Активен'
        self.fields['order'].label = 'Порядок сортировки'
