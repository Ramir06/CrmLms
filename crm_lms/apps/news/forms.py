from django import forms
from .models import News


class NewsForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Студенты могут создавать только для студентов или всех
        if user and user.role == 'student':
            self.fields['audience'].choices = [
                ('students', 'Студенты'),
                ('all', 'Все')
            ]
            
            # Студенты не могут публиковать без модерации
            self.fields['is_published'].widget.attrs.update({
                'disabled': 'disabled',
                'title': 'Требуется модерация администратора'
            })
            
            # Устанавливаем организацию студента
            if hasattr(user, 'student_profile') and user.student_profile.organization:
                self.initial['organization'] = user.student_profile.organization
    
    class Meta:
        model = News
        fields = ['title', 'content', 'image', 'audience', 'is_published']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 6}),
            'audience': forms.Select(attrs={'class': 'form-select'}),
            'is_published': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
