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
    """최상위 도메인 접속 시 나타나는 포탈 화면 (로그인 통합 + 개선사항 게시판)"""
    if request.method == "POST":
        if "logout" in request.POST:
            auth_logout(request)
            return redirect('/')
        
        # 개선사항 요청 작성 처리
        if "improvement_title" in request.POST and request.user.is_authenticated:
            from as_app.models import ImprovementRequest
            title = request.POST.get("improvement_title", "").strip()
            content = request.POST.get("improvement_content", "").strip()
            if title and content:
                ImprovementRequest.objects.create(
                    title=title,
                    content=content,
                    author=request.user,
                )
            return redirect('/')

        # 개선사항 삭제 처리 (작성자 본인 또는 관리자만)
        if "delete_request_id" in request.POST and request.user.is_authenticated:
            from as_app.models import ImprovementRequest
            try:
                req_id = int(request.POST.get("delete_request_id"))
                req_obj = ImprovementRequest.objects.get(pk=req_id)
                if req_obj.author == request.user or request.user.is_superuser:
                    req_obj.delete()
            except (ValueError, ImprovementRequest.DoesNotExist):
                pass
            return redirect('/')

        # 개선사항 완료 처리 (관리자만)
        if "complete_request_id" in request.POST and request.user.is_superuser:
            from as_app.models import ImprovementRequest
            try:
                req_id = int(request.POST.get("complete_request_id"))
                ImprovementRequest.objects.filter(pk=req_id).update(
                    status=ImprovementRequest.Status.COMPLETED
                )
            except (ValueError, ImprovementRequest.DoesNotExist):
                pass
            return redirect('/')

        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            auth_login(request, form.get_user())
            return redirect('/')
    else:
        form = AuthenticationForm(request)

    # 개선사항 요청 목록 (최근 10건)
    recent_requests = []
    if request.user.is_authenticated:
        from as_app.models import ImprovementRequest
        recent_requests = list(
            ImprovementRequest.objects.all()
            .select_related("author")
            .order_by("-created_at")[:10]
        )

    return render(request, 'portal.html', {
        'form': form,
        'recent_requests': recent_requests,
    })
