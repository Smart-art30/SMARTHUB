from django.shortcuts import render, redirect
from academics.models import StudentMark
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from attendance.models import StudentAttendance
from .forms import UserRegistrationForm
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.core.exceptions import PermissionDenied



def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:dashboard_redirect')

    register_form = UserRegistrationForm()

    if request.method == 'POST' and 'login_submit' in request.POST:
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')

            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('dashboard:dashboard_redirect')

        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'accounts/login.html', {
        'register_form': register_form
    })

@require_POST
def logout_view(request):
    logout(request)
    
    return redirect('accounts:login')


def register_view(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            login(request, user) 
            return redirect('dashboard')
    else:
        form = UserRegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})

@login_required
def dashboard_redirect(request):
    user = request.user

    if user.role == 'superadmin':
        return redirect('superadmin_dashboard')
    elif user.role == 'schooladmin':
        return redirect('schooladmin_dashboard')
    elif user.role == 'teacher':
        return redirect('teacher_dashboard')
    elif user.role == 'student':
        return redirect('student_dashboard')
    elif user.role == 'parent':
        return redirect('parent_dashboard')
    else:
        raise PermissionDenied

def student_report(Student, exam):
    marks = StudentMark.objects.filter(
        student =  student,
        exam_subject__exam  =  exam
    )
    total = sum(m.marks for m in marks)
    average =  total/ marks.count() if marks.exists() else 0

    return{
        'marks': marks,
        'total': total,
        'average': average,
    }
def student_attendance_summary(student):
    reords = student_attendance.objects.filter(student = student)
    present = records.filter(status='prsent').count()
    absent = records.filter(status='absent').count()
    late = records.filter(satus= 'late').count()

    return{
        'present': present,
        'absent': absent,
        'late': late,
    }
    StudentAttendance.objects.filter(
        student_class=class_obj,
        date__month = 6
    )

def student_fee_statement(student):
    invoices = Invoices.objects.filter(student=student)
    total_billed = sum(invoice.total_amount() for invoice in invoices)
    total_paid = sum(invoice.total_paid() for inv in invoices)

    return {
        'total_billed': total_billed,
        'total_paid ': total_paid,
        'balance' :total_billed - total_paid
    }