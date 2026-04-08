from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Course, CourseStudent, TicketTariff, TicketBalance, TicketTransaction


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['title', 'subject', 'status', 'mentor', 'start_date', 'capacity', 'students_link']
    list_filter = ['status', 'format', 'is_archived']
    search_fields = ['title', 'subject']
    prepopulated_fields = {'slug': ('title',)}
    
    def students_link(self, obj):
        """Ссылка на студентов курса"""
        if obj.is_unlimited:
            url = reverse('admin:course_students', args=[obj.id])
            return format_html('<a href="{}">Студенты (талоны)</a>', url)
        else:
            url = f'/admin/courses/coursestudent/?course__id__exact={obj.id}'
            return format_html('<a href="{}">Студенты</a>', url)
    students_link.short_description = 'Студенты'
    
    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('<int:course_id>/students/', self.admin_site.admin_view(self.course_students_view), name='course_students'),
        ]
        return custom_urls + urls
    
    def course_students_view(self, request, course_id):
        """Представление для отображения студентов курса с талонами"""
        from django.shortcuts import render, get_object_or_404
        course = get_object_or_404(Course, id=course_id)
        
        # Если курс бесконечный, показываем талоны
        if course.is_unlimited:
            students_data = []
            for cs in course.course_students.select_related('student', 'ticket_balance').all():
                balance = getattr(cs, 'ticket_balance', None)
                tickets_info = f"{balance.remaining_tickets}" if balance else "0"
                students_data.append({
                    'student': cs.student,
                    'phone': cs.student.phone,
                    'tickets': tickets_info,
                    'status': cs.get_status_display(),
                    'cs_id': cs.id
                })
            
            return render(request, 'admin/course_students_tickets.html', {
                'course': course,
                'students_data': students_data,
                'opts': self.model._meta,
            })
        else:
            # Для обычных курсов перенаправляем на стандартную страницу
            from django.http import HttpResponseRedirect
            return HttpResponseRedirect(f'/admin/courses/coursestudent/?course__id__exact={course_id}')
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'slug', 'subject', 'status', 'description')
        }),
        ('Менторы', {
            'fields': ('mentor', 'assistant_mentor')
        }),
        ('Расписание', {
            'fields': ('start_date', 'end_date', 'duration_months', 'days_of_week', 
                      'lesson_start_time', 'lesson_end_time', 'room', 'format')
        }),
        ('Финансы и вместимость', {
            'fields': ('price', 'capacity', 'is_unlimited')
        }),
        ('Онлайн доступ', {
            'fields': ('online_lesson_link', 'chat_link'),
            'classes': ('collapse',)
        }),
        ('Дополнительно', {
            'fields': ('color', 'is_archived')
        }),
    )


@admin.register(CourseStudent)
class CourseStudentAdmin(admin.ModelAdmin):
    list_display = ['student', 'course', 'status', 'joined_at']
    list_filter = ['status', 'course']
    search_fields = ['student__full_name', 'course__title']


@admin.register(TicketTariff)
class TicketTariffAdmin(admin.ModelAdmin):
    list_display = ['title', 'lessons_count', 'price_per_lesson', 'total_price', 'is_active']
    list_filter = ['is_active', 'lessons_count']
    search_fields = ['title']
    readonly_fields = ['total_price']


@admin.register(TicketBalance)
class TicketBalanceAdmin(admin.ModelAdmin):
    list_display = ['enrollment', 'total_tickets', 'used_tickets', 'remaining_tickets']
    readonly_fields = ['enrollment', 'total_tickets', 'used_tickets']
    
    def remaining_tickets(self, obj):
        return obj.remaining_tickets
    remaining_tickets.short_description = 'Осталось талонов'


@admin.register(TicketTransaction)
class TicketTransactionAdmin(admin.ModelAdmin):
    list_display = ['enrollment', 'transaction_type', 'quantity', 'price_per_ticket', 'created_at', 'created_by']
    list_filter = ['transaction_type', 'created_at']
    search_fields = ['enrollment__student__full_name', 'comment']
    readonly_fields = ['created_at']
