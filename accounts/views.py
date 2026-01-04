from django.shortcuts import render, redirect
from accounts.models import StudentMark, student_attendance


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
def student_attendance _summary(student):
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