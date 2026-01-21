from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from  .models import StudentAttendance
from students.models import Student
from schools.models import SchoolClass
from accounts.decorators import role_required


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
    students =  Student.objects.filter(school=school)

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
    attendance =  get_object_or_404(
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
    classes =  SchoolClass.objects.filter(school=school)

    selected_class =  None
    students =  []
    date = timezone.now().date()

    if request.method == 'POST'and 'load students' in request.POST:
        class_id = request.POST.get('student_class')
        date = request.POST.get('date')

        selected_class = get_object_or_404(
            SchoolClass, id = class_id, school=school
        )
        students = Student.objects.filter(
            school=school,
            student_class=selected_class
        )
        for student in students:
            status = request.POST.get(f'status_{student.id}')
            remarks = request.POST.get(f'remarks_{student.id}', '')

            StudentAttendance.objects.update_or_create(
                student=student,
                date =  date,
                defaults={
                    'school': school,
                    'student_class':student_class,
                    'status':status,
                    'remarks': remarks,
                    'marked_by': request.user.teacher
                }
            )
            messages.success(request, 'Bulk attendance saved successfully.')
            return redirect('attendance_list')
    return render(request, 'attendance/bulk_attendance.html', {
        'classes': classes,
        'students': students,
        'selected_class': selected_class,
        'date': date,
        'status_choices': StudentAttendance.STATUS_CHOICES

    })

@login_required
def student_attendance_report(request, student_id):
    school = request.user.school
    student =  get_object_or_404(
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
            


@login_required
@role_required('teacher')
def teacher_mark(request, class_id):
    students = Student.objects.filter(student_class_id=class_id)
    student_class = SchoolClass.objects.get(id=class_id)

    if request.method == "POST":
        for student in students:
            status = request.POST.get(f"status_{student.id}")
            remarks = request.POST.get(f"remarks_{student.id}", "")

            if status:
                StudentAttendance.objects.update_or_create(
                    student=student,
                    date=timezone.now().date(),
                    defaults={
                        "status": status,
                        "remarks": remarks,
                        "teacher": request.user.teacher,
                    }
                )

        messages.success(request, "Attendance saved successfully.")
        return redirect("dashboard:teacher_dashboard")

    return render(request, "attendance/teacher_mark.html", {
        "students": students,
        "student_class": student_class,
        "status_choices": StudentAttendance.STATUS_CHOICES, 
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