from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import LoginForm, UserProfileForm


def login_view(request):
    if request.user.is_authenticated:
        if request.user.is_student:
            return redirect('students:dashboard')
        return redirect('dashboard:index')

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

    return render(request, 'auth/login.html', {'form': form})


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
