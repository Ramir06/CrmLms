from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from apps.core.mixins import super_admin_required
from .forms import LoginForm, UserProfileForm, RoleForm
from .models import UserAccount, Role, CustomUser


def login_view(request):
    print(f"DEBUG: login_view called, method={request.method}")
    
    if request.user.is_authenticated:
        print("DEBUG: User already authenticated")
        if request.user.is_student:
            return redirect('students:dashboard')
        return redirect('dashboard:index')

    print("DEBUG: Rendering login form")
    form = LoginForm(request, data=request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            if user.is_student:
                next_url = request.GET.get('next', 'students:dashboard')
            else:
                next_url = request.GET.get('next', 'dashboard:index')
            return redirect(next_url)
        else:
            messages.error(request, 'Неверный email или пароль.')

    print("DEBUG: About to render template")
    try:
        response = render(request, 'auth/login.html', {'form': form})
        print("DEBUG: Template rendered successfully")
        return response
    except Exception as e:
        print(f"DEBUG: Template rendering failed: {e}")
        raise


def logout_view(request):
    logout(request)
    return redirect('accounts:login')


@login_required
def profile_view(request):
    form = UserProfileForm(request.POST or None, request.FILES or None, instance=request.user)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, 'Профиль обновлён.')
            return redirect('accounts:profile')

    return render(request, 'auth/profile.html', {'form': form})


@login_required
def add_account_view(request):
    """Добавление нового аккаунта в мультиаккаунт"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        name = request.POST.get('name', f'Аккаунт {username}')
        
        # Проверка, является ли пользователь админом или суперадмином
        is_admin = request.user.role in ('admin', 'superadmin')
        
        if is_admin and password == 'dummy_password':
            # Для админов - поиск пользователя без проверки пароля
            try:
                user = CustomUser.objects.get(username=username)
            except CustomUser.DoesNotExist:
                messages.error(request, f'Пользователь с логином "{username}" не найден')
                return redirect('accounts:manage_accounts')
        else:
            # Для обычных пользователей - аутентификация по паролю
            user = authenticate(request, username=username, password=password)
            if user is None:
                messages.error(request, 'Неверный логин или пароль')
                return redirect('accounts:manage_accounts')
        
        # Проверка, что пользователь не добавляет сам себя
        if user == request.user:
            messages.error(request, 'Нельзя добавить свой текущий аккаунт')
            return redirect('accounts:manage_accounts')
        
        # Проверка, что аккаунт еще не добавлен
        if UserAccount.objects.filter(user=request.user, account_user=user).exists():
            messages.error(request, 'Этот аккаунт уже добавлен')
            return redirect('accounts:manage_accounts')
        
        # Создание связи между аккаунтами
        UserAccount.objects.create(
            user=request.user,
            account_user=user,
            name=name
        )
        
        messages.success(request, f'Аккаунт "{name}" успешно добавлен')
        return redirect('accounts:manage_accounts')
    
    return render(request, 'auth/add_account.html')


@login_required
def manage_accounts_view(request):
    """Управление мультиаккаунтами"""
    accounts = UserAccount.objects.filter(user=request.user, is_active=True)
    return render(request, 'auth/manage_accounts.html', {'accounts': accounts})


@login_required
@require_POST
def switch_account_view(request, account_id):
    """Переключение между аккаунтами"""
    account = get_object_or_404(UserAccount, id=account_id, user=request.user, is_active=True)
    
    # Отметить аккаунт как использованный
    account.mark_as_used()
    
    # Аутентификация и вход в аккаунт
    user = account.account_user
    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
    
    messages.success(request, f'Переключено на аккаунт "{account.name}"')
    
    # Перенаправление в зависимости от роли
    if user.is_student:
        return redirect('students:dashboard')
    else:
        return redirect('dashboard:index')


@login_required
@require_POST
def remove_account_view(request, account_id):
    """Удаление аккаунта из мультиаккаунтов"""
    account = get_object_or_404(UserAccount, id=account_id, user=request.user)
    
    account_name = account.name
    account.delete()
    
    messages.success(request, f'Аккаунт "{account_name}" удален')
    return redirect('accounts:manage_accounts')


@login_required
def api_accounts_list(request):
    """API для получения списка аккаунтов"""
    try:
        accounts = UserAccount.objects.filter(user=request.user, is_active=True).select_related('account_user')
        
        accounts_data = []
        for account in accounts:
            user = account.account_user
            try:
                accounts_data.append({
                    'id': account.id,
                    'name': account.name,
                    'username': user.username,
                    'display_name': user.get_display_name(),
                    'role': user.get_role_display(),
                    'avatar_url': user.get_avatar_url(),
                    'last_used': account.last_used.isoformat() if account.last_used else None,
                })
            except Exception as user_error:
                print(f"Error processing user {user.id}: {user_error}")
                # Добавляем базовые данные если методы не работают
                accounts_data.append({
                    'id': account.id,
                    'name': account.name,
                    'username': getattr(user, 'username', 'Unknown'),
                    'display_name': getattr(user, 'username', 'Unknown'),
                    'role': 'Unknown',
                    'avatar_url': None,
                    'last_used': account.last_used.isoformat() if account.last_used else None,
                })
        
        return JsonResponse({'accounts': accounts_data})
    
    except Exception as e:
        print(f"API accounts error: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'accounts': []})  # Возвращаем пустой список вместо ошибки


@login_required
@super_admin_required
def roles_list(request):
    """Список всех ролей"""
    roles = Role.objects.all().order_by('name')
    
    context = {
        'roles': roles,
        'page_title': 'Управление ролями',
    }
    return render(request, 'admin/accounts/roles_list.html', context)


@login_required
@super_admin_required
def role_create(request):
    """Создание новой роли"""
    if request.method == 'POST':
        form = RoleForm(request.POST)
        if form.is_valid():
            role = form.save()
            messages.success(request, f'Роль "{role.name}" успешно создана.')
            return redirect('accounts:roles_list')
    else:
        form = RoleForm()
    
    context = {
        'form': form,
        'page_title': 'Создание роли',
    }
    return render(request, 'admin/accounts/role_form.html', context)


@login_required
@super_admin_required
def role_edit(request, pk):
    """Редактирование роли"""
    role = get_object_or_404(Role, pk=pk)
    
    if request.method == 'POST':
        form = RoleForm(request.POST, instance=role)
        if form.is_valid():
            role = form.save()
            messages.success(request, f'Роль "{role.name}" успешно обновлена.')
            return redirect('accounts:roles_list')
    else:
        form = RoleForm(instance=role)
    
    context = {
        'form': form,
        'role': role,
        'page_title': f'Редактирование роли: {role.name}',
    }
    return render(request, 'admin/accounts/role_form.html', context)


@login_required
@super_admin_required
@require_POST
def role_delete(request, pk):
    """Удаление роли"""
    role = get_object_or_404(Role, pk=pk)
    
    # Проверяем, что роль не используется
    if role.customuser_set.exists():
        messages.error(request, f'Нельзя удалить роль "{role.name}", так как она используется пользователями.')
        return redirect('accounts:roles_list')
    
    role_name = role.name
    role.delete()
    messages.success(request, f'Роль "{role_name}" успешно удалена.')
    return redirect('accounts:roles_list')
