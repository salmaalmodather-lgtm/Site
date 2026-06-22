import json

from django.contrib.auth import login as auth_login, logout as auth_logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.decorators.http import require_http_methods

from .forms import SignUpForm, TeacherForm, StyledAuthenticationForm
from .models import Teacher, ContentItem
from .seed_data import seed_teacher_items


# ---------------------------------------------------------------------------
# Auth Views
# ---------------------------------------------------------------------------

class SignUpView(View):
    template_name = "core/signup.html"

    def get(self, request):
        if request.user.is_authenticated:
            return redirect("dashboard_redirect")
        return render(request, self.template_name, {"form": SignUpForm()})

    def post(self, request):
        # ← طلب JSON من الفرونت
        if request.content_type == "application/json":
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                return JsonResponse({"error": "بيانات غير صحيحة"}, status=400)

            form = SignUpForm(data)
            if form.is_valid():
                user = form.save()
                auth_login(request, user)
                teacher = getattr(user, "teacher", None)
                return JsonResponse({
                    "user_id":      user.id,
                    "email":        user.email,
                    "teacher_name": teacher.name if teacher else "",
                })
            else:
                first_error = next(iter(form.errors.values()))[0]
                return JsonResponse({"error": first_error}, status=400)

        # ← طلب HTML عادي
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            return redirect("add_teacher")
        return render(request, self.template_name, {"form": form})


class CustomLoginView(LoginView):
    template_name = "core/login.html"
    authentication_form = StyledAuthenticationForm
    redirect_authenticated_user = True

    def post(self, request, *args, **kwargs):
        # ← طلب JSON من الفرونت
        if request.content_type == "application/json":
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                return JsonResponse({"error": "بيانات غير صحيحة"}, status=400)

            email    = data.get("email", "").strip()
            password = data.get("password", "")

            # Django بيستخدم username للـ authenticate
            # نجيب الـ user عن طريق الـ email الأول
            from django.contrib.auth.models import User
            try:
                username = User.objects.get(email__iexact=email).username
            except User.DoesNotExist:
                return JsonResponse({"error": "البريد الإلكتروني أو كلمة المرور غير صحيحة"}, status=400)

            user = authenticate(request, username=username, password=password)
            if user is None:
                return JsonResponse({"error": "البريد الإلكتروني أو كلمة المرور غير صحيحة"}, status=400)

            auth_login(request, user)
            teacher = getattr(user, "teacher", None)
            return JsonResponse({
                "user_id":      user.id,
                "email":        user.email,
                "teacher_name": teacher.name if teacher else "",
                "subject":      getattr(teacher, "subject", "") if teacher else "",
            })

        # ← طلب HTML عادي
        return super().post(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy("dashboard_redirect")


def logout_view(request):
    auth_logout(request)
    if request.content_type == "application/json":
        return JsonResponse({"ok": True})
    return redirect("login")


# ---------------------------------------------------------------------------
# Onboarding: add teacher name
# ---------------------------------------------------------------------------

@login_required
def dashboard_redirect(request):
    if hasattr(request.user, "teacher"):
        return redirect("dashboard")
    return redirect("add_teacher")


@login_required
def add_teacher(request):
    # لو اليوزر عنده معلم بالفعل
    if hasattr(request.user, "teacher"):
        if request.content_type == "application/json":
            teacher = request.user.teacher
            return JsonResponse({
                "teacher_name": teacher.name,
                "subject":      getattr(teacher, "subject", ""),
            })
        return redirect("dashboard")

    if request.method == "POST":
        # ← طلب JSON من الفرونت
        if request.content_type == "application/json":
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                return JsonResponse({"error": "بيانات غير صحيحة"}, status=400)

            # الفرونت بيبعت "teacher_name" لكن TeacherForm بيتوقع "name"
            form_data = {"name": data.get("teacher_name", "").strip()}
            form = TeacherForm(form_data)
            if form.is_valid():
                teacher         = form.save(commit=False)
                teacher.user    = request.user
                teacher.save()
                seed_teacher_items(teacher)
                return JsonResponse({
                    "teacher_name": teacher.name,
                    "subject":      data.get("subject", ""),
                })
            else:
                first_error = next(iter(form.errors.values()))[0]
                return JsonResponse({"error": first_error}, status=400)

        # ← طلب HTML عادي
        form = TeacherForm(request.POST)
        if form.is_valid():
            teacher      = form.save(commit=False)
            teacher.user = request.user
            teacher.save()
            seed_teacher_items(teacher)
            return redirect("dashboard")
    else:
        form = TeacherForm()

    return render(request, "core/add_teacher.html", {"form": form})


# ---------------------------------------------------------------------------
# Dashboard page
# ---------------------------------------------------------------------------

@login_required
def dashboard(request):
    if not hasattr(request.user, "teacher"):
        return redirect("add_teacher")
    teacher = request.user.teacher
    return render(request, "core/dashboard.html", {"teacher": teacher})


# ---------------------------------------------------------------------------
# JSON API
# ---------------------------------------------------------------------------

def _get_teacher_or_404(request):
    return request.user.teacher


@login_required
@require_http_methods(["GET"])
def api_list_items(request):
    teacher = _get_teacher_or_404(request)
    items   = [item.to_dict() for item in teacher.items.all()]
    return JsonResponse({"items": items, "teacher_name": teacher.name})


@login_required
@require_http_methods(["POST"])
def api_create_item(request):
    teacher = _get_teacher_or_404(request)
    data    = json.loads(request.body)
    item    = ContentItem.objects.create(
        teacher=teacher,
        week=int(data.get("week", 1)),
        type=data.get("type", "meme"),
        text=data.get("text", "").strip(),
        status=data.get("status", "pending"),
    )
    return JsonResponse({"item": item.to_dict()})


@login_required
@require_http_methods(["PUT", "PATCH"])
def api_update_item(request, item_id):
    teacher = _get_teacher_or_404(request)
    try:
        item = teacher.items.get(id=item_id)
    except ContentItem.DoesNotExist:
        return JsonResponse({"error": "غير موجود"}, status=404)

    data = json.loads(request.body)
    if "week"   in data: item.week   = int(data["week"])
    if "type"   in data: item.type   = data["type"]
    if "text"   in data: item.text   = data["text"]
    if "status" in data: item.status = data["status"]
    item.save()
    return JsonResponse({"item": item.to_dict()})


@login_required
@require_http_methods(["DELETE"])
def api_delete_item(request, item_id):
    teacher = _get_teacher_or_404(request)
    deleted, _ = teacher.items.filter(id=item_id).delete()
    if not deleted:
        return JsonResponse({"error": "غير موجود"}, status=404)
    return JsonResponse({"ok": True})


@login_required
@require_http_methods(["POST"])
def api_reset_items(request):
    teacher = _get_teacher_or_404(request)
    teacher.items.all().delete()
    seed_teacher_items(teacher)
    items = [item.to_dict() for item in teacher.items.all()]
    return JsonResponse({"items": items})