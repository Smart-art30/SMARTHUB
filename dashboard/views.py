from django.shortcuts import render
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from accounts.models import  Teacher
from schools.models import School
from students.models import Student, Parent
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

def superadmin_dashboard(request):
    total_schools = School.objects.count()
    total_users = Student.objects.count() + Teacher.objects.count() + Parent.objects.count()
    return render(request, 'dashboard/superadmin.html', {'total_schools': total_schools, 'total_users': total_users})

def schooladmin_dashboard(request):
    school = request.user.school
    total_students = Students.objects.filter(school=school).count()
    total_teachers = Teacher.objects.filter(school=school).count()
    return render(request, 'dashboard/schooladmin.html',{'total_students': total_students, 'total_teachers': total_teachers})

def teacher_dashboard(request):
    student = request.user.teacher
    subjects = teacher.user.subject_set.all()
    return render(request, 'dashboard/teacher.html', {'subjects': subjects})

def student_dashboard(request):
    student =  request.user.student
    return render(request, 'dashboard/student.html', {'student': student})

def parent_dashboard(request):
    parent = request.user.parent
    students = parent.srudents.all()
    return render(request, 'dashboard/parent.html', {'students': students})

