from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from accounts.decorators import role_required
from .models import Teacher
from schools.models import SchoolClass

@login_required
@role_required('schooladmin')
def teacher_list(request):
    teachers= Teacher.objects.filter(school=request.user.school)
    return render(request, 'teachers/teacher_list.html', {'teacher': teacher})

@login_required
@role_required('schooladmin')
def teacher_add(request):
    if request.method=='POST':
        user_id = request.POST.get('user')
        staff_id = request.POST.get('staff_id')

        Teacher.objects.create(
            user_id=user_id,
            school=request.user.school,
            staff_id=staff_id
        )
        return redirect('teacher_list')
    return render(request, 'teachers/teacher_add.html')

@login_required
def teacher_detail(request,pk):
    teacher=get_object_or_404(Teacher, pk=pk)
    return render(request, 'teachers/teacher_detail.html', {'teacher': teacher})