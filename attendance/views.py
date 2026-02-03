from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from  .models import StudentAttendance
from students.models import Student
from schools.models import SchoolClass
from accounts.decorators import role_required
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Count




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
    teacher = request.user.teacher
    today = timezone.now().date()

    student_class = get_object_or_404(
        SchoolClass,
        id=class_id,
        school=teacher.school
    )

   
    if StudentAttendance.objects.filter(
        student_class=student_class,
        date=today
    ).exists():
        messages.warning(
            request,
            "Attendance for this class has already been marked today."
        )
        return redirect("dashboard:teacher_dashboard")

    students = Student.objects.filter(
        student_class=student_class,
        school=teacher.school
    )

    if request.method == "POST":
        for student in students:
            status = request.POST.get(f"status_{student.id}")
            remarks = request.POST.get(f"remarks_{student.id}", "")

            if status:
                StudentAttendance.objects.create(
                    student=student,
                    student_class=student_class,
                    school=teacher.school,
                    date=today,
                    status=status,
                    remarks=remarks,
                    marked_by=teacher,
                )

        messages.success(request, "Attendance marked successfully.")
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

       
        attendance, created = StudentAttendance.objects.get_or_create(
            student=student,
            date=timezone.now().date(),
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

    total_students = records.values('student').distinct().count()

    status_summary = records.values('status').annotate(total=Count('id'))

    context = {
        'classes': classes,
        'records': records.order_by('student_class', 'student', '-date'),
        'selected_class_id': selected_class_id,
        'selected_date': selected_date,
        'total_students': total_students,
        'status_summary': status_summary,
    }

    return render(request, 'attendance/attendance_dashboard.html', context)