from django.shortcuts import render,redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
import teachers.views as teacher_views
from teachers.models import Teacher,TeacherSubjectAssignment
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
from notifications.models import Notification
from academics.models import Subject,AcademicTerm
from django.db.models import Count





@login_required
def dashboard_redirect(request):
    user = request.user

    # 🔹 Django superuser (admin panel or dashboard)
    if user.is_superuser or user.role == 'superadmin':
        return redirect('dashboard:superadmin_dashboard')

    # 🔹 School Admin
    if user.role == 'schooladmin':
        return redirect('dashboard:schooladmin_dashboard')

    # 🔹 Teacher (NO approval check)
    if user.role == 'teacher':
        if hasattr(user, 'teacher'):
            return redirect('dashboard:teacher_dashboard')

        return render(
            request,
            'dashboard/profile_pending.html',
            {'message': 'Teacher profile not created. Contact admin.'}
        )

    # 🔹 Student
    if user.role == 'student':
        if hasattr(user, 'student'):
            return redirect('dashboard:student_dashboard')

        return render(
            request,
            'dashboard/profile_pending.html',
            {'message': 'Student profile not created.'}
        )

    # 🔹 Parent
    if user.role == 'parent':
        if hasattr(user, 'parent'):
            return redirect('dashboard:parent_dashboard')

        return render(
            request,
            'dashboard/profile_pending.html',
            {'message': 'Parent profile not created.'}
        )

    # 🔻 Fallback
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
    subject_count = Subject.objects.filter(school=school).count()

   
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
        'subject_count': subject_count,
    }

    return render(request, 'dashboard/schooladmin.html', context)



@login_required
@role_required('teacher')
def teacher_dashboard(request):
    teacher = request.user.teacher

    active_term = AcademicTerm.objects.filter(is_active=True).first()

    assignments = (
        TeacherSubjectAssignment.objects
        .filter(teacher=teacher)
        .select_related('school_class', 'subject')
        .annotate(student_count=Count('school_class__student'))
        .order_by('school_class__name', 'subject__name')
    )

  
    classes = {}
    for a in assignments:
        class_id = a.school_class.id
        if class_id not in classes:
            classes[class_id] = {
                'class': a.school_class,
                'student_count': a.student_count
            }

    classes = classes.values()

    total_classes = len(classes)
    total_subjects = assignments.values('subject').distinct().count()
    workload = assignments.count()

    notifications = Notification.objects.filter(
        user=request.user,
        school=teacher.school
    ).order_by('-created_at')[:5]

    context = {
        'teacher': teacher,
        'assignments': assignments,
        'classes': classes, 
        'notifications': notifications,
        'active_term': active_term,
        'total_classes': total_classes,
        'total_subjects': total_subjects,
        'workload': workload,
    }

    return render(request, 'dashboard/teacher.html', context)


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



@login_required
@role_required('teacher')
def teacher_profile_edit(request):
    teacher = request.user.teacher

    if request.method == 'POST':
        teacher.phone = request.POST.get('phone')
        teacher.qualification = request.POST.get('qualification')
        teacher.specialization = request.POST.get('specialization')
        teacher.save()
        return redirect('teacher_dashboard')

    return render(request, 'dashboard/teacher_profile_edit.html', {
        'teacher': teacher
    })