from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from accounts.decorators import role_required
from .models import Teacher
from django.contrib.auth import get_user_model


User = get_user_model()
# -----------------------------
# List all teachers
# -----------------------------
@login_required
@role_required('schooladmin')
def teacher_list(request):
    teachers = Teacher.objects.filter(school=request.user.school)
    return render(request, 'teachers/teacher_list.html', {'teachers': teachers})

# -----------------------------
# Add teacher
# -----------------------------
@login_required
@role_required('schooladmin')
def teacher_add(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        employee_id = request.POST.get('employee_id')
        phone = request.POST.get('phone')
        designation = request.POST.get('designation')
        qualification = request.POST.get('qualification')
        specialization = request.POST.get('specialization')
        date_of_birth = request.POST.get('date_of_birth')
        gender = request.POST.get('gender')
        profile_picture = request.FILES.get('profile_picture')

        if first_name and last_name and email and employee_id:
            user = User.objects.create(
                username=email,
                first_name=first_name,
                last_name=last_name,
                email=email,
                password=make_password('defaultpassword123')
            )

            teacher = Teacher.objects.create(
                user=user,
                school=request.user.school,
                employee_id=employee_id,
                phone=phone,
                designation=designation,
                qualification=qualification,
                specialization=specialization,
                date_of_birth=date_of_birth if date_of_birth else None,
                gender=gender,
            )

            if profile_picture:
                teacher.profile_picture = profile_picture
                teacher.save()

            return redirect('teacher_list')

    return render(request, 'teachers/teacher_add.html')

# -----------------------------
# Teacher detail
# -----------------------------
@login_required
@role_required('schooladmin')
def teacher_detail(request, pk):
    teacher = get_object_or_404(Teacher, pk=pk)
    return render(request, 'teachers/teacher_detail.html', {'teacher': teacher})
