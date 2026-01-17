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