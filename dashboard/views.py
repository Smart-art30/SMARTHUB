from django.shortcuts import render,redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
import teachers.views as teacher_views
from teachers.models import Teacher
from schools.models import School
from django.http import Http404
from students.models import Student
from finance.models import Invoice, Payment
from attendance.models import StudentAttendance, TeacherAttendance, SchoolClass
from accounts.decorators import role_required
from students.models import Parent
from django.contrib.auth import get_user_model
from students.models import Student
from academics.models import Exam
from students.models import Student 


@login_required
def dashboard_redirect(request):
    user = request.user

    
    if user.is_superuser:
        return redirect('superadmin_dashboard')

    
    if user.role == 'superadmin':
        return redirect('superadmin_dashboard')

    elif user.role == 'schooladmin':
        return redirect('schooladmin_dashboard')

    elif user.role == 'teacher':
        if hasattr(user, 'teacher'):
            teacher = user.teacher
            if not teacher.is_approved:
                return render(request, 'dashboard/profile_pending.html', {
                    'message': 'Your teacher profile is pending admin approval.'
                })
            return redirect('teacher_dashboard')
        return render(request, 'dashboard/profile_pending.html', {
            'message': 'Teacher profile not created. Contact admin.'
        })

    elif user.role == 'student':
        if hasattr(user, 'student'):
            return redirect('student_dashboard')
        return render(request, 'dashboard/profile_pending.html', {
            'message': 'Student profile not created.'
        })

    elif user.role == 'parent':
        if hasattr(user, 'parent'):
            return redirect('parent_dashboard')
        return render(request, 'dashboard/profile_pending.html', {
            'message': 'Parent profile not created.'
        })

    # Fallback
    return redirect('login')



User = get_user_model()

@login_required
@role_required('superadmin')
def superadmin_dashboard(request):
    total_schools = School.objects.count()

    total_users = User.objects.exclude(is_superuser=True).count()

    return render(request, 'dashboard/superadmin.html', {
        'total_schools': total_schools,
        'total_users': total_users,
    })


@login_required
@role_required('schooladmin')
def schooladmin_dashboard(request):
    user = request.user
    school = getattr(user, 'school', None)

    if not school:
        return render(request, 'dashboard/error.html', {
            'error': 'No school assigned to your account. Contact the system administrator.'
        })

    classes = SchoolClass.objects.filter(school=school).order_by('name', 'stream')
    total_students = Student.objects.filter(school=school).count()
    total_teachers = Teacher.objects.filter(school=school).count()
    total_invoices = Invoice.objects.filter(fee_structure__school=school).count()
    total_payments = Payment.objects.filter(
        invoice__fee_structure__school=school
    ).aggregate(total=Sum('amount'))['total'] or 0
    recent_payments = Payment.objects.filter(
        invoice__fee_structure__school=school
    ).order_by('-payment_date')[:5]

    students = Student.objects.filter(school=school)
    exams = Exam.objects.all()

   
    student = students.first() if students.exists() else None
    exam = exams.first() if exams.exists() else None

    context = {
        'school': school,
        'classes': classes,
        'total_students': total_students,
        'total_teachers': total_teachers,
        'total_invoices': total_invoices,
        'total_payments': total_payments,
        'recent_payments': recent_payments,
        'student': student,
        'exam': exam,
    }

    return render(request, 'dashboard/schooladmin.html', context)



@login_required
@role_required('teacher')
def teacher_dashboard(request):
    teacher = request.user.teacher  

    classes = teacher.assigned_classes.all()
    subjects = teacher.user.subject_set.all()

    return render(request, 'dashboard/teacher.html', {
        'teacher': teacher,
        'classes': classes,
        'subjects': subjects,
    })

@login_required
@role_required('student')
def student_dashboard(request):
    student = request.user.student
    return render(request, 'dashboard/student.html', {
        'student': student
    })

@login_required
@role_required('parent')
def parent_dashboard(request):
    parent = request.user.parent
    students = parent.students.all()
    return render(request, 'dashboard/parent.html', {
        'students': students
    })


