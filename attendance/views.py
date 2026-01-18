from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from  .models import StudentAttendance
from students.models import Student
from schools.models import SchoolClass

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
        'status_choice': StudentAttendance.STATUS_CHOICES
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
            status = request.POST.get(f'status_{studemt.id}')
            remarks = request.POST.get(f'remarks_{studemt.id}', '')

            StudentAttendance.objects.updated_or_create(
                studemt=student,
                date =  date,
                defaults={
                    'school': school,
                    'studemt_class':studemt_class,
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
    return render(request, 'attendance/student_report.html',{
        'student': student,
        'records': records
    })

@login_required
def class_attendance_report(request, class_id):
    school = request.user.school
    studemt_class = get_object_or_404(
        SchoolClass, id=class_id, school=school
    )
    records = StudentAttendance.objects.filter(
        studemt_class=studemt_class
    )
    return render(request, 'attendance/class_report.html',{
        'studemt_class': student_class,
        'records': records
    })
            


