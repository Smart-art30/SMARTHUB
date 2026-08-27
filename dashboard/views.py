from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from django.core.exceptions import PermissionDenied

from academics.models import StudentMark, Exam, Subject, AcademicTerm
from attendance.models import (
    StudentAttendance,
    TeacherAttendance,
    SchoolClass,
)
from finance.models import Invoice, Payment
from notifications.models import Notification
from schools.models import School
from students.models import Student, Parent
from teachers.models import Teacher, TeacherSubjectAssignment

from accounts.decorators import role_required


User = get_user_model()


# ============================================================
# DASHBOARD REDIRECT
# ============================================================

@login_required
def dashboard_redirect(request):
    """
    Send the authenticated user to the correct dashboard
    according to their role.
    """

    user = request.user

    # Superuser always gets Super Admin dashboard
    if user.is_superuser:
        return redirect("dashboard:superadmin_dashboard")

    role = getattr(user, "role", None)

    if role == "superadmin":
        return redirect("dashboard:superadmin_dashboard")

    elif role == "chiefexercutiveofficer":
        return redirect("dashboard:ceo_dashboard")

    elif role == "schooladmin":
        return redirect("dashboard:schooladmin_dashboard")

    elif role in ("bursar", "accountant"):
        return redirect("finance:finance_dashboard")

    elif role == "teacher":
        if hasattr(user, "teacher"):
            return redirect("dashboard:teacher_dashboard")

        return render(
            request,
            "dashboard/profile_pending.html",
            {
                "message": (
                    "Your teacher profile has not yet been created. "
                    "Please contact the school administrator."
                )
            },
        )

    elif role == "student":
        if hasattr(user, "student"):
            return redirect("dashboard:student_dashboard")

        return render(
            request,
            "dashboard/profile_pending.html",
            {
                "message": (
                    "Your student profile has not yet been created. "
                    "Please contact the school administrator."
                )
            },
        )

    elif role == "parent":
        if hasattr(user, "parent"):
            return redirect("dashboard:parent_dashboard")

        return render(
            request,
            "dashboard/profile_pending.html",
            {
                "message": (
                    "Your parent profile has not yet been created. "
                    "Please contact the school administrator."
                )
            },
        )

    # Unknown or missing role
    return render(
        request,
        "dashboard/profile_pending.html",
        {
            "message": (
                "Your account does not have a valid role assigned. "
                "Please contact the system administrator."
            )
        },
    )


# ============================================================
# SUPER ADMIN DASHBOARD
# ============================================================

@login_required
@role_required("superadmin")
def superadmin_dashboard(request):

    total_schools = School.objects.count()

    total_users = (
        User.objects
        .exclude(is_superuser=True)
        .count()
    )

    context = {
        "total_schools": total_schools,
        "total_users": total_users,
    }

    return render(
        request,
        "dashboard/superadmin.html",
        context,
    )


# ============================================================
# CEO DASHBOARD
# ============================================================

@login_required
@role_required("chiefexercutiveofficer")
def ceo_dashboard(request):

    total_schools = School.objects.count()

    total_users = (
        User.objects
        .exclude(is_superuser=True)
        .count()
    )

    context = {
        "total_schools": total_schools,
        "total_users": total_users,
    }

    return render(
        request,
        "dashboard/ceo_dashboard.html",
        context,
    )


# ============================================================
# SCHOOL ADMIN DASHBOARD
# ============================================================

@login_required
@role_required("schooladmin")
def schooladmin_dashboard(request):

    user = request.user

    school = getattr(user, "school", None)

    if school is None:
        return render(
            request,
            "dashboard/error.html",
            {
                "error": (
                    "No school is assigned to your account. "
                    "Please contact the system administrator."
                )
            },
        )

    classes = (
        SchoolClass.objects
        .filter(school=school)
        .order_by("name", "stream")
    )

    total_students = (
        Student.objects
        .filter(school=school)
        .count()
    )

    total_teachers = (
        Teacher.objects
        .filter(school=school)
        .count()
    )

    total_invoices = (
        Invoice.objects
        .filter(fee_structure__school=school)
        .count()
    )

    total_payments = (
        Payment.objects
        .filter(invoice__fee_structure__school=school)
        .aggregate(total=Sum("amount"))
        ["total"]
        or 0
    )

    recent_payments = (
        Payment.objects
        .filter(invoice__fee_structure__school=school)
        .select_related("invoice")
        .order_by("-payment_date")[:5]
    )

    students = Student.objects.filter(school=school)

    exams = (
        Exam.objects
        .filter(school=school)
        .order_by("-created_at")
    )

    subject_count = (
        Subject.objects
        .filter(school=school)
        .count()
    )

    student = students.first()
    exam = exams.first()

    context = {
        "school": school,
        "classes": classes,
        "total_students": total_students,
        "total_teachers": total_teachers,
        "total_invoices": total_invoices,
        "total_payments": total_payments,
        "recent_payments": recent_payments,
        "students": students,
        "exams": exams,
        "student": student,
        "exam": exam,
        "subject_count": subject_count,
    }

    return render(
        request,
        "dashboard/schooladmin.html",
        context,
    )


# ============================================================
# TEACHER DASHBOARD
# ============================================================

@login_required
@role_required("teacher")
def teacher_dashboard(request):

    teacher = getattr(request.user, "teacher", None)

    if teacher is None:
        return render(
            request,
            "dashboard/profile_pending.html",
            {
                "message": (
                    "Your teacher profile has not yet been created. "
                    "Please contact the school administrator."
                )
            },
        )

    active_term = (
        AcademicTerm.objects
        .filter(is_active=True)
        .first()
    )

    assignments = (
        TeacherSubjectAssignment.objects
        .filter(teacher=teacher)
        .select_related(
            "school_class",
            "subject",
        )
        .annotate(
            student_count=Count(
                "school_class__student",
                distinct=True,
            )
        )
        .order_by(
            "school_class__name",
            "subject__name",
        )
    )

    # Group assignments by class
    classes_dict = {}

    for assignment in assignments:

        class_id = assignment.school_class_id

        if class_id not in classes_dict:

            classes_dict[class_id] = {
                "class": assignment.school_class,
                "student_count": assignment.student_count,
            }

    classes = list(classes_dict.values())

    total_classes = len(classes)

    total_subjects = (
        assignments
        .values("subject")
        .distinct()
        .count()
    )

    workload = assignments.count()

    notifications = (
        Notification.objects
        .filter(
            user=request.user,
            school=teacher.school,
        )
        .order_by("-created_at")[:5]
    )

    context = {
        "teacher": teacher,
        "assignments": assignments,
        "classes": classes,
        "notifications": notifications,
        "active_term": active_term,
        "total_classes": total_classes,
        "total_subjects": total_subjects,
        "workload": workload,
    }

    return render(
        request,
        "dashboard/teacher.html",
        context,
    )


# ============================================================
# STUDENT DASHBOARD
# ============================================================

@login_required
@role_required("student")
def student_dashboard(request):

    student = getattr(request.user, "student", None)

    if student is None:
        return render(
            request,
            "dashboard/profile_pending.html",
            {
                "message": (
                    "Your student profile has not yet been created. "
                    "Please contact the school administrator."
                )
            },
        )

    return render(
        request,
        "dashboard/student.html",
        {
            "student": student,
        },
    )


# ============================================================
# PARENT DASHBOARD
# ============================================================

TERM_ORDER = {
    "Opener": 1,
    "Mid-term": 2,
    "End-term": 3,
}


@login_required
@role_required("parent")
def parent_dashboard(request):

    parent = getattr(request.user, "parent", None)

    if parent is None:
        return render(
            request,
            "dashboard/profile_pending.html",
            {
                "message": (
                    "Your parent profile has not yet been created. "
                    "Please contact the school administrator."
                )
            },
        )

    children = (
        parent.students
        .all()
        .select_related(
            "student_class",
            "school",
        )
    )

    children_data = []

    for child in children:

        exams = Exam.objects.filter(
            school=child.school
        )

        latest_exam = None

        if exams.exists():

            latest_exam = max(
                exams,
                key=lambda exam: (
                    exam.year,
                    TERM_ORDER.get(
                        exam.term,
                        0,
                    ),
                ),
            )

        # Marks
        if latest_exam:

            marks = StudentMark.objects.filter(
                student=child,
                exam=latest_exam,
            )

        else:

            marks = StudentMark.objects.none()

        # Attendance
        attendance = StudentAttendance.objects.filter(
            student=child
        )

        total_days = attendance.count()

        present_days = attendance.filter(
            status="present"
        ).count()

        absent_days = attendance.filter(
            status="absent"
        ).count()

        late_days = attendance.filter(
            status="late"
        ).count()

        attendance_percentage = (
            present_days / total_days * 100
            if total_days
            else 0
        )

        # Pending invoices
        pending_invoices = Invoice.objects.filter(
            student=child,
            is_paid=False,
        )

        children_data.append(
            {
                "student": child,
                "latest_exam": latest_exam,
                "marks": marks,
                "attendance": {
                    "total_days": total_days,
                    "present_days": present_days,
                    "absent_days": absent_days,
                    "late_days": late_days,
                    "percentage": attendance_percentage,
                },
                "pending_invoices": pending_invoices,
            }
        )

    return render(
        request,
        "dashboard/parent.html",
        {
            "children_data": children_data,
        },
    )


# ============================================================
# TEACHER PROFILE EDIT
# ============================================================

@login_required
@role_required("teacher")
def teacher_profile_edit(request):

    teacher = getattr(
        request.user,
        "teacher",
        None,
    )

    if teacher is None:
        return render(
            request,
            "dashboard/profile_pending.html",
            {
                "message": (
                    "Your teacher profile has not yet been created."
                )
            },
        )

    if request.method == "POST":

        teacher.phone = request.POST.get(
            "phone",
            ""
        )

        teacher.qualification = request.POST.get(
            "qualification",
            ""
        )

        teacher.specialization = request.POST.get(
            "specialization",
            ""
        )

        teacher.save()

        return redirect(
            "dashboard:teacher_dashboard"
        )

    return render(
        request,
        "dashboard/teacher_profile_edit.html",
        {
            "teacher": teacher,
        },
    )


# ============================================================
# HELPER: STUDENT REPORT
# ============================================================

def student_report(student, exam):

    marks = StudentMark.objects.filter(
        student=student,
        exam=exam,
    )

    total = sum(
        mark.marks
        for mark in marks
    )

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


# ============================================================
# HELPER: STUDENT ATTENDANCE SUMMARY
# ============================================================

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


# ============================================================
# HELPER: STUDENT FEE STATEMENT
# ============================================================

def student_fee_statement(student):

    invoices = Invoice.objects.filter(
        student=student
    )

    total_billed = sum(
        invoice.total_amount()
        for invoice in invoices
    )

    total_paid = sum(
        invoice.total_paid()
        for invoice in invoices
    )

    return {
        "total_billed": total_billed,
        "total_paid": total_paid,
        "balance": total_billed - total_paid,
    }