from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.auth.decorators import login_required
from accounts.decorators import role_required
from .models import Student
from schools.models import SchoolClass
from django.contrib.auth import get_user_model
from .forms import StudentAddForm
import secrets
from django.contrib import messages
from django.db import IntegrityError




User = get_user_model()

@login_required
@role_required('schooladmin')
def student_list(request):
    students = Student.objects.filter(school=request.user.school)
    return render(request, 'students/students_list.html',{'students':students} )


@login_required
@role_required('schooladmin')
def student_add(request):
    school = request.user.school  # Make sure logged-in user has a school
    classes = SchoolClass.objects.filter(school=school)  # Only classes in this school

    if request.method == "POST":
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        username = request.POST.get('username')
        admission = request.POST.get('admission_number')
        class_id = request.POST.get('student_class')
        dob = request.POST.get('date_of_birth')
        gender = request.POST.get('gender')
        photo = request.FILES.get('photo')

        
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
            return redirect('student_add')

        if Student.objects.filter(admission_number=admission, school=school).exists():
            messages.error(request, f"Admission number {admission} already exists in this school.")
            return redirect('student_add')

    
        password = secrets.token_urlsafe(8)

        try:
            
            user = User.objects.create_user(
                username=username,
                password=password,
                first_name=first_name,
                last_name=last_name,
                role='student',
                school=school,
                is_active=True,
                must_change_password=True
            )

            
            Student.objects.create(
                user=user,
                school=school,
                student_class_id=class_id,
                admission_number=admission,
                date_of_birth=dob or None,
                gender=gender or None,
                photo=photo or None
            )

        except IntegrityError:
            messages.error(request, "Could not create student due to duplicate data.")
            return redirect('student_add')

        messages.success(request, f"Student added successfully. Temporary password: {password}")
        return redirect('student_list')

    return render(request, 'students/student_add.html', {'classes': classes})

@login_required
def student_detail(request, pk):
    student= get_object_or_404(Student, pk=pk)

    return render(request, 'students/student_detail.html', {'student':student})