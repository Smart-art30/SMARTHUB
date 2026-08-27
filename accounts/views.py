from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.views.decorators.http import require_POST

from academics.models import StudentMark
from attendance.models import StudentAttendance
from .forms import UserRegistrationForm


# =========================================================
# LOGIN
# =========================================================

def login_view(request):

    # Already logged in
    if request.user.is_authenticated:
        return redirect("dashboard:dashboard_redirect")

    if request.method == "POST":

        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        if not username or not password:

            messages.error(
                request,
                "Please enter both username and password."
            )

            return render(
                request,
                "accounts/login.html",
                {
                    "username": username,
                }
            )

        try:

            user = authenticate(
                request,
                username=username,
                password=password
            )

            if user is not None:

                login(request, user)

                return redirect(
                    "dashboard:dashboard_redirect"
                )

            messages.error(
                request,
                "Invalid username or password. Please check your details and try again."
            )

        except Exception as e:

            print("LOGIN ERROR:", type(e).__name__, str(e))

            messages.error(
                request,
                "A system error occurred during login. Please try again."
            )

    return render(
        request,
        "accounts/login.html"
    )


# =========================================================
# REGISTER
# =========================================================

def register_view(request):

    # Don't allow an already logged-in user to register
    if request.user.is_authenticated:
        return redirect("dashboard:dashboard_redirect")

    if request.method == "POST":

        form = UserRegistrationForm(request.POST)

        if form.is_valid():

            try:

                user = form.save()

                # Automatically log the new user in
                login(request, user)

                messages.success(
                    request,
                    "Account created successfully. Welcome to SmartHub!"
                )

                return redirect(
                    "dashboard:dashboard_redirect"
                )

            except Exception as e:

                print("REGISTRATION ERROR:")
                print(type(e).__name__)
                print(str(e))

                messages.error(
                    request,
                    "Unable to create the account. Please check your details and try again."
                )

        else:

            messages.error(
                request,
                "Please correct the errors below."
            )

    else:

        form = UserRegistrationForm()

    return render(
        request,
        "accounts/register.html",
        {
            "form": form
        }
    )


# =========================================================
# LOGOUT
# =========================================================

@require_POST
def logout_view(request):

    logout(request)

    messages.success(
        request,
        "You have been logged out successfully."
    )

    return redirect(
        "accounts:login"
    )


# =========================================================
# DASHBOARD REDIRECT
# =========================================================

@login_required
def dashboard_redirect(request):

    user = request.user

    if user.role == "superadmin":
        return redirect("superadmin_dashboard")

    elif user.role == "schooladmin":
        return redirect("schooladmin_dashboard")

    elif user.role == "teacher":
        return redirect("teacher_dashboard")

    elif user.role == "student":
        return redirect("student_dashboard")

    elif user.role == "parent":
        return redirect("parent_dashboard")

    else:
        raise PermissionDenied(
            "Your account does not have a valid role."
        )


# =========================================================
# STUDENT REPORT
# =========================================================

def student_report(student, exam):

    marks = StudentMark.objects.filter(
        student=student,
        exam_subject__exam=exam
    )

    total = sum(m.marks for m in marks)

    average = (
        total / marks.count()
        if marks.exists()
        else 0
    )

    return {
        "marks": marks,
        "total": total,
        "average": average,
    }


# =========================================================
# STUDENT ATTENDANCE
# =========================================================

def student_attendance_summary(student):

    records = StudentAttendance.objects.filter(
        student=student
    )

    present = records.filter(
        status="present"
    ).count()

    absent = records.filter(
        status="absent"
    ).count()

    late = records.filter(
        status="late"
    ).count()

    return {
        "present": present,
        "absent": absent,
        "late": late,
    }