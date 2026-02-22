from django.shortcuts import render, redirect
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth import login as auth_login, logout as auth_logout

def signup_view(request):
    """회원가입 뷰 - 가입 승인을 위해 is_active 플래그를 False로 저장"""
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False # 관리자 승인 전까지 로그인 불가
            user.save()
            return redirect('/?signup=ok')
    else:
        form = UserCreationForm()
    
    return render(request, 'signup.html', {'form': form})

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
