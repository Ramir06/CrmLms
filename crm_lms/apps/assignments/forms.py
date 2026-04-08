from django import forms
from ckeditor.widgets import CKEditorWidget
from .models import Assignment

class AssignmentForm(forms.ModelForm):
    class Meta:
        model = Assignment
        fields = ['section', 'title', 'description', 'max_score', 'due_date', 'order', 'is_required', 'is_visible']
        widgets = {
            'description': CKEditorWidget(attrs={'class': 'django-ckeditor-widget'}),
        }

    def __init__(self, *args, **kwargs):
        course = kwargs.pop('course', None)
        super().__init__(*args, **kwargs)
        
        if course:
            self.fields['section'].queryset = self.fields['section'].queryset.filter(course=course)
