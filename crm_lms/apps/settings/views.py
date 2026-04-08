from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.urls import reverse
from django.core.mail import send_mail
from django.conf import settings as django_settings
from django.contrib.auth import get_user_model
from .models import FooterNavigationLink
import secrets
import string

from .models import SystemSetting, SectionOrder, PaymentMethod, FooterContent
from apps.courses.models import Course
from apps.lectures.models import Section
from apps.core.mixins import admin_required

User = get_user_model()


def is_admin(user):
    return user.is_authenticated and user.role in ('admin', 'superadmin')


def generate_password(length=12):
    """Generate a secure random password."""
    alphabet = string.ascii_letters + string.digits
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    return password


@login_required
@user_passes_test(is_admin)
def update_system_settings(request):
    """Update system settings."""
    if request.method == 'POST':
        # Получаем настройки из формы
        menu_position = request.POST.get('menu_position', 'left')
        student_fields = request.POST.getlist('student_fields')
        
        # Сохраняем настройки в базу данных
        SystemSetting.objects.update_or_create(
            key='menu_position',
            defaults={'value': menu_position, 'description': 'Положение меню в системе'}
        )
        
        # Сохраняем поля формы студента как JSON
        import json
        SystemSetting.objects.update_or_create(
            key='student_form_fields',
            defaults={'value': json.dumps(student_fields), 'description': 'Поля формы создания студента'}
        )
        
        # Применяем настройки немедленно (если нужно)
        apply_system_settings()
        
        messages.success(request, 'Настройки системы сохранены и применены')
        return redirect('settings:dashboard')
    
    return redirect('settings:dashboard')


def apply_system_settings():
    """Применяет системные настройки к работе системы."""
    # Получаем настройки положения меню
    menu_position = SystemSetting.get_value('menu_position', 'left')
    
    # Здесь можно добавить логику применения настроек
    # Например, можно сохранить в кэш или глобальные переменные
    from django.core.cache import cache
    cache.set('menu_position', menu_position, timeout=3600)  # кэшируем на час
    
    # Получаем настройки полей формы
    student_fields_json = SystemSetting.get_value('student_form_fields', '[]')
    try:
        import json
        student_fields = json.loads(student_fields_json)
        cache.set('student_form_fields', student_fields, timeout=3600)
    except json.JSONDecodeError:
        cache.set('student_form_fields', ['login', 'password', 'email'], timeout=3600)


def get_student_form_fields():
    """Возвращает список полей для формы создания студента."""
    from django.core.cache import cache
    
    # Сначала пробуем получить из кэша
    fields = cache.get('student_form_fields')
    if fields is not None:
        return fields
    
    # Если в кэше нет, получаем из базы
    student_fields_json = SystemSetting.get_value('student_form_fields', '["login", "password", "email"]')
    try:
        import json
        fields = json.loads(student_fields_json)
    except json.JSONDecodeError:
        fields = ['login', 'password', 'email']
    
    # Сохраняем в кэш
    cache.set('student_form_fields', fields, timeout=3600)
    return fields


def get_menu_position():
    """Возвращает положение меню."""
    from django.core.cache import cache
    
    # Сначала пробуем получить из кэша
    position = cache.get('menu_position')
    if position is not None:
        return position
    
    # Если в кэше нет, получаем из базы
    position = SystemSetting.get_value('menu_position', 'left')
    cache.set('menu_position', position, timeout=3600)
    return position


@login_required
@user_passes_test(is_admin)
def settings_dashboard(request):
    """Main settings dashboard."""
    # Загружаем текущие настройки
    current_menu_position = get_menu_position()
    current_student_fields = get_student_form_fields()
    
    # Get courses with their sections for ordering
    courses = Course.objects.all().prefetch_related('sections')
    
    context = {
        'courses': courses,
        'page_title': 'Настройки системы',
        'active_menu': 'settings',
        'current_menu_position': current_menu_position,
        'current_student_fields': current_student_fields,
        'current_fields_count': len(current_student_fields),
    }
    return render(request, 'admin/settings/dashboard.html', context)


@login_required
@user_passes_test(is_admin)
def create_staff_user(request):
    """Create a new staff user and send credentials via email."""
    if request.method == 'POST':
        email = request.POST.get('email')
        role = request.POST.get('role')
        
        if not email or not role:
            messages.error(request, 'Email и роль обязательны')
            return redirect('settings:dashboard')
        
        # Check if user already exists
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Пользователь с таким email уже существует')
            return redirect('settings:dashboard')
        
        # Generate password
        password = generate_password()
        
        try:
            # Create user first
            user = User.objects.create_user(
                email=email,
                password=password,
                role=role,
                is_active=True
            )
            
            # Prepare email
            login_url = request.build_absolute_uri(reverse('accounts:login'))
            
            # HTML email
            html_message = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>Добро пожаловать в IT Academy LMS</title>
            </head>
            <body style="font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f4f4f4;">
                <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 0 20px rgba(0,0,0,0.1);">
                    <div style="text-align: center; margin-bottom: 30px;">
                        <h1 style="color: #7367f0; margin: 0;">IT Academy</h1>
                        <h2 style="color: #5e5873; margin: 10px 0 0 0;">Система управления обучением</h2>
                    </div>
                    
                    <div style="background-color: #f0eeff; padding: 20px; border-radius: 8px; margin: 20px 0;">
                        <h3 style="color: #7367f0; margin-top: 0;">Добро пожаловать!</h3>
                        <p style="color: #6e6b7b; margin-bottom: 20px;">
                            Вас добавили в систему управления обучением IT Academy. 
                            Ниже ваши учетные данные для входа в систему.
                        </p>
                        
                        <div style="background-color: white; padding: 15px; border-radius: 5px; margin: 15px 0;">
                            <p style="margin: 5px 0;"><strong>Логин:</strong> {email}</p>
                            <p style="margin: 5px 0;"><strong>Пароль:</strong> <span style="background-color: #e8e5fc; padding: 2px 8px; border-radius: 3px; font-family: monospace;">{password}</span></p>
                            <p style="margin: 5px 0;"><strong>Роль:</strong> {user.get_role_display()}</p>
                        </div>
                    </div>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{login_url}" style="background-color: #7367f0; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">Войти в систему</a>
                    </div>
                    
                    <div style="background-color: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <p style="margin: 0; color: #856404;">
                            <strong>Важно:</strong> После первого входа обязательно смените пароль в настройках профиля.
                        </p>
                    </div>
                    
                    <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #ebe9f1;">
                        <p style="color: #6e6b7b; margin: 0; font-size: 14px;">Это автоматическое уведомление. Пожалуйста, не отвечайте на это письмо.</p>
                    </div>
                </div>
            </body>
            </html>
            """.format(email=email, password=password, user=user, login_url=login_url)
            
            # Plain text email
            plain_message = f"""
Здравствуйте!

Вас добавили в систему управления обучением IT Academy.

Ваши учетные данные:
Логин: {email}
Пароль: {password}
Роль: {user.get_role_display()}

Ссылка для входа: {login_url}

После первого входа обязательно смените пароль в настройках профиля.

Это автоматическое уведомление. Пожалуйста, не отвечайте на это письмо.
            """.format(email=email, password=password, user=user, login_url=login_url)
            
            # Send email with detailed error handling
            try:
                send_mail(
                    subject='Добро пожаловать в IT Academy LMS',
                    message=plain_message,
                    from_email=django_settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    html_message=html_message,
                    fail_silently=False,
                )
                messages.success(request, f'Пользователь {email} создан. Данные отправлены на email.')
            except Exception as email_error:
                # Log the error but don't delete the user
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to send email to {email}: {str(email_error)}")
                
                # Try with console backend as fallback
                try:
                    from django.core.mail import get_connection
                    connection = get_connection(backend='django.core.mail.backends.console.EmailBackend')
                    send_mail(
                        subject='Добро пожаловать в IT Academy LMS',
                        message=plain_message,
                        from_email=django_settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[email],
                        html_message=html_message,
                        connection=connection,
                        fail_silently=False,
                    )
                    messages.warning(request, f'Пользователь {email} создан. Email выведен в консоль (SMTP ошибка: {str(email_error)})')
                except:
                    messages.warning(request, f'Пользователь {email} создан, но email не отправлен. Ошибка: {str(email_error)}')
                    messages.info(request, f'Временный пароль для {email}: {password}')
            
        except Exception as e:
            # If user creation fails, show error
            messages.error(request, f'Ошибка при создании пользователя: {str(e)}')
        
        return redirect('settings:dashboard')
    
    return redirect('settings:dashboard')


@login_required
@user_passes_test(is_admin)
@require_POST
def update_section_order(request):
    """Update section ordering for a course."""
    course_id = request.POST.get('course_id')
    orders = request.POST.getlist('orders[]')
    
    if not course_id or not orders:
        return JsonResponse({'error': 'Missing data'}, status=400)
    
    course = get_object_or_404(Course, pk=course_id)
    
    for i, section_id in enumerate(orders):
        try:
            section = Section.objects.get(pk=section_id, course=course)
            order_obj, created = SectionOrder.objects.get_or_create(
                course=course,
                section=section,
                defaults={'order': i}
            )
            if not created:
                order_obj.order = i
                order_obj.save()
        except Section.DoesNotExist:
            continue
    
    return JsonResponse({'ok': True})


@login_required
@user_passes_test(is_admin)
def payment_methods_list(request):
    """Список способов оплаты."""
    payment_methods = PaymentMethod.objects.all()
    context = {
        'payment_methods': payment_methods,
        'page_title': 'Способы оплаты',
        'active_menu': 'settings',
    }
    return render(request, 'admin/settings/payment_methods/list.html', context)


@login_required
@user_passes_test(is_admin)
def payment_method_create(request):
    """Создание способа оплаты."""
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        is_active = request.POST.get('is_active') == 'on'
        sort_order = request.POST.get('sort_order', 0)
        
        if name:
            PaymentMethod.objects.create(
                name=name,
                description=description,
                is_active=is_active,
                sort_order=sort_order
            )
            messages.success(request, 'Способ оплаты добавлен')
        else:
            messages.error(request, 'Название способа оплаты обязательно')
        
        return redirect('settings:payment_methods_list')
    
    return render(request, 'admin/settings/payment_methods/form.html', {
        'page_title': 'Добавить способ оплаты',
        'active_menu': 'settings',
    })


@login_required
@user_passes_test(is_admin)
def payment_method_edit(request, pk):
    """Редактирование способа оплаты."""
    payment_method = get_object_or_404(PaymentMethod, pk=pk)
    
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        is_active = request.POST.get('is_active') == 'on'
        sort_order = request.POST.get('sort_order', 0)
        
        if name:
            payment_method.name = name
            payment_method.description = description
            payment_method.is_active = is_active
            payment_method.sort_order = sort_order
            payment_method.save()
            messages.success(request, 'Способ оплаты обновлен')
        else:
            messages.error(request, 'Название способа оплаты обязательно')
        
        return redirect('settings:payment_methods_list')
    
    return render(request, 'admin/settings/payment_methods/form.html', {
        'payment_method': payment_method,
        'page_title': 'Редактировать способ оплаты',
        'active_menu': 'settings',
    })


@login_required
@user_passes_test(is_admin)
def payment_method_delete(request, pk):
    """Удаление способа оплаты."""
    payment_method = get_object_or_404(PaymentMethod, pk=pk)
    
    if request.method == 'POST':
        payment_method.delete()
        messages.success(request, 'Способ оплаты удален')
    
    return redirect('settings:payment_methods_list')


@login_required
@user_passes_test(is_admin)
@require_POST
def payment_method_toggle(request, pk):
    """Включение/отключение способа оплаты."""
    payment_method = get_object_or_404(PaymentMethod, pk=pk)
    payment_method.is_active = not payment_method.is_active
    payment_method.save()
    
    return JsonResponse({
        'ok': True,
        'is_active': payment_method.is_active
    })


def footer_password_check(request):
    """Проверка пароля для доступа к футеру."""
    if request.method == 'POST':
        password = request.POST.get('password')
        stored_password = SystemSetting.get_value('footer_password', '')
        
        if password == stored_password:
            request.session['footer_access'] = True
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'error': 'Неверный пароль'})
    
    return JsonResponse({'success': False, 'error': 'Метод не разрешен'})


@login_required
def footer_editor(request):
    """Редактор футера с парольной защитой."""
    if not request.session.get('footer_access'):
        if request.method == 'POST':
            password = request.POST.get('password')
            stored_password = SystemSetting.get_value('footer_password', '')
            
            if password == stored_password:
                request.session['footer_access'] = True
            else:
                return render(request, 'admin/settings/footer_password.html', {
                    'error': 'Неверный пароль'
                })
        else:
            return render(request, 'admin/settings/footer_password.html')
    
    footer_content = FooterContent.objects.first()
    if not footer_content:
        footer_content = FooterContent.objects.create()
    
    nav_links = FooterNavigationLink.objects.all().order_by('order', 'title')
    
    if request.method == 'POST':
        footer_content.title = request.POST.get('title', 'ОкууTrack')
        footer_content.description = request.POST.get('description', '')
        footer_content.public_offer = request.POST.get('public_offer', '')
        footer_content.contact_info = request.POST.get('contact_info', '')
        footer_content.copyright_text = request.POST.get('copyright_text', '© 2024 ОкууTrack. Все права защищены.')
        footer_content.is_active = request.POST.get('is_active') == 'on'
        
        # Parse JSON fields
        import json
        try:
            if request.POST.get('social_links'):
                footer_content.social_links = json.loads(request.POST.get('social_links', '{}'))
            if request.POST.get('additional_links'):
                footer_content.additional_links = json.loads(request.POST.get('additional_links', '{}'))
        except json.JSONDecodeError:
            pass
        
        footer_content.save()
        messages.success(request, 'Настройки футера успешно обновлены!')
        return redirect('settings:footer_editor')
    
    context = {
        'footer_content': footer_content,
        'nav_links': nav_links,
        'page_title': 'Редактор футера',
        'active_menu': 'settings',
    }
    return render(request, 'admin/settings/footer_editor.html', context)


@login_required
@admin_required
def footer_navigation_list(request):
    """Список навигационных ссылок футера."""
    nav_links = FooterNavigationLink.objects.all().order_by('order', 'title')
    
    context = {
        'nav_links': nav_links,
        'page_title': 'Навигационные ссылки футера',
        'active_menu': 'settings',
    }
    return render(request, 'admin/settings/footer_navigation_list.html', context)


@login_required
@admin_required
def footer_navigation_add(request):
    """Добавление навигационной ссылки футера."""
    if request.method == 'POST':
        title = request.POST.get('title')
        slug = request.POST.get('slug')
        content = request.POST.get('content', '')
        order = request.POST.get('order', 0)
        is_active = request.POST.get('is_active') == 'on'
        
        if title and slug:
            nav_link = FooterNavigationLink.objects.create(
                title=title,
                slug=slug,
                content=content,
                order=order,
                is_active=is_active
            )
            messages.success(request, f'Навигационная ссылка "{nav_link.title}" успешно создана!')
            return redirect('settings:footer_navigation_list')
        else:
            messages.error(request, 'Заполните обязательные поля!')
    
    context = {
        'page_title': 'Добавить навигационную ссылку',
        'active_menu': 'settings',
    }
    return render(request, 'admin/settings/footer_navigation_form.html', context)


