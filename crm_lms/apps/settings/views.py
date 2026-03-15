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
import secrets
import string

from .models import SystemSetting, SectionOrder
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
def settings_dashboard(request):
    """Main settings dashboard."""
    # Get courses with their sections for ordering
    courses = Course.objects.all().prefetch_related('sections')
    
    context = {
        'courses': courses,
        'page_title': 'Настройки системы',
        'active_menu': 'settings',
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


