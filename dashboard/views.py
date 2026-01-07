from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from teachers.models import  Teacher
from schools.models import School
from students.models import Student, Parent
from finance.models import Invoice, Payment
from attendance.models import StudentAttendance, TeacherAttendance


# def home(request):
#     return render(request, 'dashboard/home.html')

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
        return redirect('login')

@login_required
def superadmin_dashboard(request):
    total_schools = School.objects.count()
    total_users = Student.objects.count() + Teacher.objects.count() + Parent.objects.count()
    return render(request, 'dashboard/superadmin.html', {
        'total_schools': total_schools, 
        'total_users': total_users
        })

@login_required
def schooladmin_dashboard(request):
    school = request.user.school
    total_students = Student.objects.filter(school=school).count()
    total_teachers = Teacher.objects.filter(school=school).count()
    total_invoices = Invoice.objects.filter(student__school=school).count()
    total_payments = sum(p.amount for p in Payment.objects.filter(invoice__student__school=school))
    return render(request, 'dashboard/schooladmin.html',{
        'total_students': total_students, 
        'total_teachers': total_teachers,
        'total_invoices': total_invoices,
        'total_payments': total_payments
        
        })

@login_required
def teacher_dashboard(request):
    teacher = request.user.teacher
    classes = teacher.assigned_classes.all()
    subjects = teacher.user.subject_set.all()
    return render(request, 'dashboard/teacher.html', {
        'subjects': subjects,
        'classes': classes
        })

@login_required
def student_dashboard(request):
    student =  request.user.student
    return render(request, 'dashboard/student.html',
    {'student': student})

@login_required
def parent_dashboard(request):
    parent = request.user.parent
    students = parent.students.all()
    return render(request, 'dashboard/parent.html', {
        'students': students})

