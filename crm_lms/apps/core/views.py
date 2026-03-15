from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required


@login_required
def index_redirect(request):
    return redirect('dashboard:index')
