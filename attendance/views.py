from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import StudentAttendance
from students.models import Student
from schools.models import SchoolClass
from accounts.decorators import role_required
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Count, Q
from django.db import transaction
from datetime import datetime, timedelta
from django.core.cache import cache


@login_required
def attendance_list(request):
    school = request.user.school
    attendances = StudentAttendance.objects.filter(
        school=school
    )
    return render(request, 'attendance/attendance_list.html', {
        'attendances': attendances
    })

@login_required
def attendance_detail(request, pk):
    attendance = get_object_or_404(
        StudentAttendance,
        pk=pk,
        school=request.user.school
    )
    return render(request, 'attendance/attendance_detail.html',{
        'attendance': attendance
    })

@login_required
def attendance_add(request):
    school = request.user.school
    classes = SchoolClass.objects.filter(school=school)
    students = Student.objects.filter(school=school)

    if request.method == 'POST':
        student_id = request.POST.get('student')
        class_id = request.POST.get('student_class')
        date = request.POST.get('date')
        status = request.POST.get('status')
        remarks = request.POST.get('remarks')

        student = get_object_or_404(Student, id=student_id, school=school)
        student_class = get_object_or_404(SchoolClass, id=class_id, school=school)

        attendance, created = StudentAttendance.objects.get_or_create(
            student=student,      
            date=date,
            defaults={
                'school': school,
                'student_class': student_class,
                'status': status,
                'remarks': remarks,
                'marked_by': request.user.teacher
            }
        )

        if not created:
            messages.error(request, 'Attendance already marked for this student today.')
            return redirect('attendance:attendance_add')  

    return render(request, 'attendance/attendance_add.html', {
        'students': students,
        'classes': classes,
        'today': timezone.now().date(),
        'status_choices': StudentAttendance.STATUS_CHOICES,
    })


@login_required
def attendance_edit(request, pk):
    attendance = get_object_or_404(
        StudentAttendance,
        pk=pk,
        school=request.user.school
    )
    if request.method == 'POST':
        attendance.status = request.POST.get('status')
        attendance.remarks = request.POST.get('remarks')
        attendance.save()

        messages.success(request, 'Attendance updated.')
        return redirect('attendance_detail', pk=attendance.pk)
    return render(request, 'attendance/attendance_edit.html', {
        'attendance': attendance,
        'status_choices': StudentAttendance.STATUS_CHOICES
    })

@login_required
def attendance_delete(request, pk):
    attendance = get_object_or_404(
        StudentAttendance,
        pk=pk,
        school=request.user.school
    )
    if request.method == 'POST':
        attendance.delete()
        messages.success(request, 'Attendance delete.')
        return redirect('attendance_list')
    return render(request, 'attendance/attendance_confirm_delete.html',{
        'attendance': attendance
    })

@login_required
def bulk_attendance(request):
    school = request.user.school
    classes = SchoolClass.objects.filter(school=school)

    selected_class = None
    students = []
    date = timezone.now().date()

    if request.method == 'POST' and 'load students' in request.POST:
        class_id = request.POST.get('student_class')
        date = request.POST.get('date')
        if not date:
            date = timezone.now().date()

        selected_class = get_object_or_404(
            SchoolClass, id=class_id, school=school
        )
        
        # Get students and automatically mark them as present
        students = Student.objects.filter(
            school=school,
            student_class=selected_class
        )
        
        # Check if register can be opened
        can_open, message, opening_count = can_open_attendance_register(request.user.teacher, selected_class, date)
        
        if not can_open:
            messages.error(request, message)
            return render(request, 'attendance/bulk_attendance.html', {
                'classes': classes,
                'students': students,
                'selected_class': selected_class,
                'date': date,
                'status_choices': StudentAttendance.STATUS_CHOICES,
                'is_locked': True,
                'lock_message': message,
                'opening_count': opening_count
            })
        
        # Auto-mark all students as present when the register is opened
        with transaction.atomic():
            for student in students:
                # Check if attendance already exists for this student today
                attendance, created = StudentAttendance.objects.get_or_create(
                    student=student,
                    date=date,
                    defaults={
                        'school': school,
                        'student_class': selected_class,
                        'status': 'present',  # Default to present
                        'remarks': 'Auto-marked present',
                        'marked_by': request.user.teacher
                    }
                )
                
                # If record already exists but was marked as something else, don't override
                # unless it's a new record
                if not created and attendance.status == 'present':
                    # Keep it as present if it was already present
                    pass

        # Increment opening count
        increment_opening_count(request.user.teacher, selected_class, date)
        new_count = get_opening_count(request.user.teacher, selected_class, date)
        
        messages.success(request, f'Attendance register opened. All students marked present by default. (Opening #{new_count})')
        
        # Check if this was the second opening (will be locked after this)
        if new_count >= 2:
            messages.warning(request, '⚠️ This is the 2nd opening. The register will now be locked. No further openings allowed.')
        
        return redirect('attendance_list')

    return render(request, 'attendance/bulk_attendance.html', {
        'classes': classes,
        'students': students,
        'selected_class': selected_class,
        'date': date,
        'status_choices': StudentAttendance.STATUS_CHOICES,
        'is_locked': False,
        'lock_message': None,
        'opening_count': 0
    })

@login_required
def student_attendance_report(request, student_id):
    school = request.user.school
    student = get_object_or_404(
        Student, id=student_id, school=school
    )
    records = StudentAttendance.objects.filter(
        student=student
    )
    return render(request, 'attendance/student_attendance_report.html',{
        'student': student,
        'records': records
    })

@login_required
def class_attendance_report(request, class_id):
    school = request.user.school
    student_class = get_object_or_404(
        SchoolClass, id=class_id, school=school
    )
    records = StudentAttendance.objects.filter(
        student_class=student_class
    )
    return render(request, 'attendance/class_report.html',{
        'student_class': student_class,
        'records': records
    })

def get_opening_count(teacher, student_class, date):
    """
    Get the number of times the register has been opened for this class today.
    Uses cache for better performance.
    """
    cache_key = f"attendance_open_{teacher.id}_{student_class.id}_{date}"
    return cache.get(cache_key, 0)

def increment_opening_count(teacher, student_class, date):
    """
    Increment the opening count for this class today.
    """
    cache_key = f"attendance_open_{teacher.id}_{student_class.id}_{date}"
    current_count = cache.get(cache_key, 0)
    cache.set(cache_key, current_count + 1, timeout=86400)  # 24 hours timeout
    return current_count + 1

def can_open_attendance_register(teacher, student_class, date):
    """
    Check if a teacher can open the attendance register for a specific class on a given date.
    Returns (can_open, message, opening_count)
    """
    opening_count = get_opening_count(teacher, student_class, date)
    
    # If already opened 2 times, block
    if opening_count >= 2:
        return False, f"This attendance register has been opened {opening_count} times today. Maximum of 2 openings allowed. ACCESS DENIED.", opening_count
    
    # Check if there are any attendance records for this class today
    records = StudentAttendance.objects.filter(
        student_class=student_class,
        date=date
    )
    
    if not records.exists():
        # No records exist, can open
        return True, "Register can be opened.", opening_count
    
    # Check if there are any records with status other than 'present' (indicates manual changes)
    manual_changes = records.exclude(status='present').exists()
    
    if manual_changes:
        return False, "This attendance register has been finalized and cannot be reopened. Please contact admin for changes.", opening_count
    
    # Check if there are auto-marked records
    auto_marked = records.filter(remarks__icontains='auto-marked')
    
    if auto_marked.exists():
        # Check if this is the first or second opening
        if opening_count == 0:
            return True, "Register can be opened.", opening_count
        elif opening_count == 1:
            return True, "Register can be opened. (Last opening allowed)", opening_count
    
    return True, "Register can be opened.", opening_count

@login_required
@role_required('teacher')
def teacher_mark(request, class_id):
    teacher = request.user.teacher
    today = timezone.now().date()

    student_class = get_object_or_404(
        SchoolClass,
        id=class_id,
        school=teacher.school
    )

    # Check if register can be opened - THIS WILL BLOCK ACCESS ON 3RD ATTEMPT
    can_open, lock_message, opening_count = can_open_attendance_register(teacher, student_class, today)
    
    # If cannot open (3rd attempt or finalized), block access completely
    if not can_open:
        messages.error(request, f"ACCESS DENIED: {lock_message}")
        
        # Log the attempt
        print(f"WARNING: Teacher {teacher.user.username} attempted to access attendance for class {student_class.name} on {today} - BLOCKED (Opening #{opening_count})")
        
        # Redirect with error
        return redirect('attendance:attendance_blocked', class_id=class_id)

    students = Student.objects.filter(
        student_class=student_class,
        school=teacher.school
    )

    # Check if attendance already exists for today
    existing_attendance = StudentAttendance.objects.filter(
        student_class=student_class,
        date=today
    )

    # Handle POST requests for updates
    if request.method == "POST":
        # Check again if register is still accessible (double-check)
        can_open_post, _, _ = can_open_attendance_register(teacher, student_class, today)
        if not can_open_post:
            messages.error(request, "ACCESS DENIED: Register was locked during processing.")
            return redirect("attendance:attendance_blocked", class_id=class_id)
            
        updated_count = 0
        with transaction.atomic():
            for student in students:
                status = request.POST.get(f"status_{student.id}")
                remarks = request.POST.get(f"remarks_{student.id}", "")

                if status:
                    # Update existing record or create if doesn't exist
                    attendance, created = StudentAttendance.objects.update_or_create(
                        student=student,
                        student_class=student_class,
                        school=teacher.school,
                        date=today,
                        defaults={
                            'status': status,
                            'remarks': remarks,
                            'marked_by': teacher,
                        }
                    )
                    updated_count += 1

        messages.success(request, f"Attendance updated for {updated_count} students.")
        return redirect("dashboard:teacher_dashboard")

    # If no attendance exists and register can be opened, auto-mark all as present
    if not existing_attendance.exists() and can_open:
        # Count this as opening the register
        with transaction.atomic():
            for student in students:
                StudentAttendance.objects.create(
                    student=student,
                    student_class=student_class,
                    school=teacher.school,
                    date=today,
                    status='present',  # Default to present
                    remarks=f'Auto-marked present when register was opened (Opening #{opening_count + 1})',
                    marked_by=teacher,
                )
        
        # Increment opening count
        new_count = increment_opening_count(teacher, student_class, today)
        
        messages.info(
            request,
            f"Attendance register opened. All {students.count()} students marked as present by default. (Opening #{new_count} of 2)"
        )
        
        # Check if this was the second opening
        if new_count >= 2:
            messages.warning(
                request,
                f"⚠️ This is the 2nd opening. The register is now LOCKED. No further access will be allowed."
            )

    return render(request, "attendance/teacher_mark.html", {
        "students": students,
        "student_class": student_class,
        "status_choices": StudentAttendance.STATUS_CHOICES,
        "today": today,
        "existing_attendance_count": existing_attendance.count(),
        "opening_count": opening_count + 1 if existing_attendance.exists() else opening_count,
        "max_openings": 2,
        "remaining_openings": 2 - (opening_count + 1 if existing_attendance.exists() else opening_count),
    })

@login_required
@role_required('teacher')
def class_attendance_report(request, class_id):
    student_class = get_object_or_404(SchoolClass, id=class_id)

    date = request.GET.get("date")

    records = StudentAttendance.objects.filter(
        student__student_class=student_class
    ).select_related("student", "marked_by")

    if date:
        records = records.filter(date=date)

    students = Student.objects.filter(student_class=student_class)

    context = {
        "student_class": student_class,
        "records": records.order_by("-date"),
        "students": students,
        "selected_date": date,
    }
    return render(
        request,
        "attendance/class_report.html",
        context
    )

@login_required
def attendance_blocked(request, class_id):
    """
    View to show when attendance is blocked (3rd attempt)
    """
    student_class = get_object_or_404(SchoolClass, id=class_id, school=request.user.school)
    today = timezone.now().date()
    
    # Get opening count
    opening_count = get_opening_count(request.user.teacher, student_class, today)
    
    return render(request, 'attendance/attendance_blocked.html', {
        'student_class': student_class,
        'today': today,
        'opening_count': opening_count,
        'max_openings': 2
    })

@csrf_exempt
def mark_attendance_ajax(request, class_id):
    if request.method == "POST":
        data = json.loads(request.body)
        student_id = data.get("student_id")
        status = data.get("status", "present")
        remarks = data.get("remarks", "")

        student = get_object_or_404(Student, id=student_id)
        school = student.school
        student_class = student.student_class
        today = timezone.now().date()
        
        # Check if register is locked for this class today
        if request.user.is_authenticated and hasattr(request.user, 'teacher'):
            teacher = request.user.teacher
            can_open, _, opening_count = can_open_attendance_register(teacher, student_class, today)
            if not can_open:
                return JsonResponse({
                    "success": False, 
                    "error": f"ACCESS DENIED: Attendance register is locked. (Opening #{opening_count})"
                }, status=403)

        # Create or update attendance record
        attendance, created = StudentAttendance.objects.get_or_create(
            student=student,
            date=today,
            defaults={
                'status': status,
                'remarks': remarks,
                'school': school,
                'student_class': student_class,
            }
        )

        if not created:
            attendance.status = status
            attendance.remarks = remarks
            attendance.save()

        return JsonResponse({"success": True, "status": status})

    return JsonResponse({"success": False}, status=400)

@login_required
@role_required('schooladmin')
def attendance_dashboard(request):
    school = request.user.school
    classes = SchoolClass.objects.filter(school=school)

    selected_class_id = request.GET.get('class')
    selected_date = request.GET.get('date')

    records = StudentAttendance.objects.filter(
        school=school
    ).select_related('student', 'student_class')

    if selected_class_id:
        records = records.filter(student_class__id=selected_class_id)

    if selected_date:
        records = records.filter(date=selected_date)

    # Convert records to a list so we can prepare class-based data
    records_list = list(
        records.order_by('student_class', 'student', '-date')
    )

    # Group records by class
    class_records = []

    for student_class in classes:
        class_students = [
            record for record in records_list
            if record.student_class_id == student_class.id
        ]

        if not class_students:
            continue

        class_records.append({
            'grouper': student_class,
            'list': class_students,
            'present_count': sum(
                1 for record in class_students
                if record.status.lower() == 'present'
            ),
            'absent_count': sum(
                1 for record in class_students
                if record.status.lower() == 'absent'
            ),
            'late_count': sum(
                1 for record in class_students
                if record.status.lower() == 'late'
            ),
        })

    total_students = records.values('student').distinct().count()

    status_summary = records.values('status').annotate(
        total=Count('id')
    )

    context = {
        'classes': classes,
        'records': records_list,
        'class_records': class_records,
        'selected_class_id': selected_class_id,
        'selected_date': selected_date,
        'total_students': total_students,
        'status_summary': status_summary,
    }

    return render(
        request,
        'attendance/attendance_dashboard.html',
        context
    )

@login_required
@role_required('teacher')
def open_attendance_register(request, class_id):
    """
    A dedicated view to explicitly open the attendance register
    and mark all students as present by default.
    """
    teacher = request.user.teacher
    today = timezone.now().date()

    student_class = get_object_or_404(
        SchoolClass,
        id=class_id,
        school=teacher.school
    )

    # Check if register can be opened - BLOCK ON 3RD ATTEMPT
    can_open, lock_message, opening_count = can_open_attendance_register(teacher, student_class, today)
    
    if not can_open:
        messages.error(request, f"ACCESS DENIED: {lock_message}")
        return redirect("attendance:attendance_blocked", class_id=class_id)

    # Check if attendance already exists for today
    existing_attendance = StudentAttendance.objects.filter(
        student_class=student_class,
        date=today
    )

    if existing_attendance.exists():
        messages.warning(
            request,
            "Attendance for this class has already been marked today. You can update individual statuses."
        )
        return redirect("attendance:teacher_mark", class_id=class_id)

    students = Student.objects.filter(
        student_class=student_class,
        school=teacher.school
    )

    # Mark all students as present
    with transaction.atomic():
        for student in students:
            StudentAttendance.objects.create(
                student=student,
                student_class=student_class,
                school=teacher.school,
                date=today,
                status='present',
                remarks=f'Auto-marked present when register was opened (Opening #{opening_count + 1})',
                marked_by=teacher,
            )

    # Increment opening count
    new_count = increment_opening_count(teacher, student_class, today)
    
    messages.success(
        request,
        f"Attendance register opened. All {students.count()} students marked as present. (Opening #{new_count} of 2)"
    )
    
    # Check if this was the second opening
    if new_count >= 2:
        messages.warning(
            request,
            "⚠️ This is the 2nd opening. The register is now LOCKED. No further access will be allowed."
        )
    
    # Redirect to the marking page
    return redirect("attendance:teacher_mark", class_id=class_id)

@login_required
@role_required('schooladmin')
def pending_attendance_report(request):
    """
    View for admin to see which classes have had their attendance marked today
    and which haven't, including lock status.
    """
    school = request.user.school
    today = timezone.now().date()
    
    classes = SchoolClass.objects.filter(school=school)
    
    class_attendance_status = []
    
    for class_obj in classes:
        attendance_today = StudentAttendance.objects.filter(
            student_class=class_obj,
            date=today
        )
        
        total_students = Student.objects.filter(
            student_class=class_obj,
            school=school
        ).count()
        
        marked_students = attendance_today.count()
        
        # Check opening count (using a default teacher - in production, get the assigned teacher)
        # For now, we'll use a sample approach
        is_locked = False
        opening_count = 0
        
        if attendance_today.exists():
            # Check if there are any manual changes
            has_manual_changes = attendance_today.exclude(status='present').exists()
            
            # Check opening count from cache
            # We need to check for all teachers - simplified approach
            from django.contrib.auth.models import User
            teachers = User.objects.filter(teacher__school=school)
            
            max_openings = 0
            for teacher_user in teachers:
                if hasattr(teacher_user, 'teacher'):
                    count = get_opening_count(teacher_user.teacher, class_obj, today)
                    if count > max_openings:
                        max_openings = count
            
            opening_count = max_openings
            
            if has_manual_changes or opening_count >= 2:
                is_locked = True
        
        class_attendance_status.append({
            'class_obj': class_obj,
            'total_students': total_students,
            'marked_students': marked_students,
            'is_complete': marked_students == total_students and total_students > 0,
            'is_partial': 0 < marked_students < total_students,
            'is_not_started': marked_students == 0,
            'is_locked': is_locked,
            'opening_count': opening_count,
            'max_openings': 2,
        })
    
    context = {
        'classes': class_attendance_status,
        'today': today,
    }
    
    return render(request, 'attendance/pending_attendance_report.html', context)

@login_required
@role_required('schooladmin')
def unlock_attendance_register(request, class_id):
    """
    Admin view to manually unlock an attendance register.
    """
    if request.method != 'POST':
        messages.error(request, "Invalid request method.")
        return redirect('attendance:pending_attendance_report')
    
    school = request.user.school
    today = timezone.now().date()
    
    student_class = get_object_or_404(
        SchoolClass,
        id=class_id,
        school=school
    )
    
    # Clear the opening count from cache for all teachers
    from django.contrib.auth.models import User
    teachers = User.objects.filter(teacher__school=school)
    
    cleared_count = 0
    for teacher_user in teachers:
        if hasattr(teacher_user, 'teacher'):
            cache_key = f"attendance_open_{teacher_user.teacher.id}_{class_id}_{today}"
            if cache.get(cache_key):
                cache.delete(cache_key)
                cleared_count += 1
    
   
    with transaction.atomic():
        StudentAttendance.objects.filter(
            student_class=student_class,
            date=today,
            remarks__icontains='auto-marked'
        ).update(
            remarks='Manually unlocked by admin. Changes can now be made.'
        )
    
    messages.success(
        request, 
        f"Attendance register for {student_class.name} has been unlocked. {cleared_count} teacher records cleared."
    )
    return redirect('attendance:pending_attendance_report')

@login_required
@role_required('teacher')
def attendance_blocked(request, class_id):
    student_class = get_object_or_404(
        SchoolClass,
        id=class_id,
        school=request.user.teacher.school
    )

    return render(
        request,
        'attendance/attendance_blocked.html',
        {
            'student_class': student_class,
        }
    )