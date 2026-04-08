from django import forms
from django.conf import settings
from .models import Event


class ColorSelectWidget(forms.Select):
    def __init__(self, attrs=None, choices=()):
        super().__init__(attrs, choices)
        self.attrs['class'] = 'form-select color-select'

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex, attrs)
        if value:
            option['attrs']['data-color'] = value
            option['attrs']['style'] = f'background-color: {value}; color: white; padding-left: 20px;'
        return option


class EventForm(forms.ModelForm):
    color = forms.ChoiceField(
        choices=Event.COLOR_CHOICES,
        initial='#28a745',
        widget=ColorSelectWidget(),
        label='Цвет'
    )

    class Meta:
        model = Event
        fields = ['title', 'description', 'date', 'start_time', 'end_time', 'target_type', 'target_user', 'color']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите название мероприятия'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Введите описание мероприятия'
            }),
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'start_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'end_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'target_type': forms.Select(attrs={
                'class': 'form-select',
                'id': 'target_type_select'
            }),
            'target_user': forms.Select(attrs={
                'class': 'form-select',
                'id': 'target_user_select'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        organization = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)
        
        if organization:
            # Фильтруем пользователей по организации через связь OrganizationMember
            from apps.accounts.models import CustomUser
            users = CustomUser.objects.filter(
                organizationmember__organization=organization,
                organizationmember__is_active=True,
                is_active=True
            ).distinct()
            self.fields['target_user'].queryset = users
        else:
            self.fields['target_user'].queryset = settings.AUTH_USER_MODEL.objects.none()
        
        # Изначально скрываем выбор пользователя
        self.fields['target_user'].widget.attrs['style'] = 'display: none;'
    
    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        target_type = cleaned_data.get('target_type')
        target_user = cleaned_data.get('target_user')
        
        # Проверяем что конец времени позже начала
        if start_time and end_time and start_time >= end_time:
            raise forms.ValidationError('Время окончания должно быть позже времени начала')
        
        # Для типа "Кому либо" обязательно нужно выбрать пользователя
        if target_type == 'custom' and not target_user:
            raise forms.ValidationError('Для типа "Кому либо" необходимо выбрать конкретного пользователя')
        
        return cleaned_data
