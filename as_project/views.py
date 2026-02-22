from django.shortcuts import render, redirect
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login as auth_login, logout as auth_logout

def portal_view(request):
    """최상위 도메인 접속 시 나타나는 포탈 화면 (로그인 통합)"""
    if request.method == "POST":
        if "logout" in request.POST:
            auth_logout(request)
            return redirect('/')
        
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            auth_login(request, form.get_user())
            return redirect('/')
    else:
        form = AuthenticationForm(request)

    return render(request, 'portal.html', {'form': form})
