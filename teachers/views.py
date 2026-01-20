from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from accounts.decorators import role_required
from .models import Teacher
from django.contrib.auth import get_user_model
import random
import string, secrets
from django.contrib import messages
from django.db import IntegrityError
from django.core.mail import send_mail
from .forms import TeacherSubjectAssignmentForm




User = get_user_model()
# -----------------------------
# List all teachers
# -----------------------------
@login_required
@role_required('schooladmin')
def teacher_list(request):
    teachers = Teacher.objects.filter(school=request.user.school)
    return render(request, 'teachers/teacher_list.html', {'teachers': teachers})


# Generate random password
def generate_random_password(length=10):
    alphabet = string.ascii_letters + string.digits + string.punctuation
    return ''.join(secrets.choice(alphabet) for _ in range(length))

# Generate unique username
def generate_unique_username(email):
    base_username = email.split('@')[0]
    username = base_username
    counter = 1
    while User.objects.filter(username=username).exists():
        username = f"{base_username}{counter}"
        counter += 1
    return username


# -----------------------------
# Generate random password
# -----------------------------
def generate_random_password(length=10):
    alphabet = string.ascii_letters + string.digits + string.punctuation
    return ''.join(secrets.choice(alphabet) for _ in range(length))


# -----------------------------
# Generate unique username
# -----------------------------
def generate_unique_username(email):
    base_username = email.split('@')[0]
    username = base_username
    counter = 1
    while User.objects.filter(username=username).exists():
        username = f"{base_username}{counter}"
        counter += 1
    return username


@login_required
@role_required('schooladmin')
def teacher_add(request):
    
    form_data = {
        'first_name': '',
        'last_name': '',
        'email': '',
        'employee_id': '',
        'phone': '',
        'designation': '',
        'qualification': '',
        'specialization': '',
        'date_of_birth': '',
        'gender': '',
    }

    if request.method == 'POST':
        
        for field in form_data:
            form_data[field] = request.POST.get(field)

      
        required_fields = ['first_name', 'last_name', 'email', 'employee_id', 'gender']
        if not all(form_data[field] for field in required_fields):
            messages.error(request, 'Please fill all required fields including gender.')
            return render(request, 'teachers/teacher_add.html', {'form_data': form_data})

        
        if Teacher.objects.filter(employee_id=form_data['employee_id']).exists():
            messages.error(request, f"A teacher with Employee ID '{form_data['employee_id']}' already exists.")
            return render(request, 'teachers/teacher_add.html', {'form_data': form_data})

        email = form_data['email']
        random_password = generate_random_password()  

        
        try:
            user = User.objects.create(
                username=email,  
                first_name=form_data['first_name'],
                last_name=form_data['last_name'],
                email=email,
                password=make_password(random_password),
                role='teacher'
            )
        except IntegrityError:
            messages.error(request, f"A user with email '{email}' already exists. Try a different email.")
            return render(request, 'teachers/teacher_add.html', {'form_data': form_data})

       
        teacher = Teacher.objects.create(
            user=user,
            school=request.user.school,
            employee_id=form_data['employee_id'],
            phone=form_data['phone'],
            designation=form_data['designation'],
            qualification=form_data['qualification'],
            specialization=form_data['specialization'],
            date_of_birth=form_data['date_of_birth'] or None,
            gender=form_data['gender'],
        )

       
        profile_picture = request.FILES.get('profile_picture')
        if profile_picture:
            teacher.profile_picture = profile_picture
            teacher.save()

        messages.success(request, 'Teacher added! Temporary credentials displayed below.')
        return render(request, 'teachers/teacher_add.html', {
            'temp_username': email,         
            'temp_password': random_password,
            'teacher_email': email,
            'form_data': form_data
        })

    return render(request, 'teachers/teacher_add.html', {'form_data': form_data})

@login_required
@role_required('schooladmin')
def teacher_detail(request, pk):
    teacher = get_object_or_404(Teacher, pk=pk)
    return render(request, 'teachers/teacher_detail.html', {'teacher': teacher})

    
@login_required
@role_required('teacher')
def teacher_profile_edit(request):
    teacher = request.user.teacher

    if request.method == 'POST':
        form = TeacherProfileForm(
            request.POST,
            request.FILES,
            instance=teacher
        )
        if form.is_valid():
            form.save()
            return redirect('teacher_dashboard')
    else:
        form = TeacherProfileForm(instance=teacher)

    return render(request, 'dashboard/teacher_profile_edit.html', {
        'form': form
    })

def add_teacher_subject(request):
    school = request.user.school 

    if request.method == 'POST':
        form = TeacherSubjectAssignmentForm(request.POST, school=school)
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.school = school  
            assignment.save()

            messages.success(request, 'Teacher assigned to subject successfully.')
            return redirect('dashboard:schooladmin_dashboard')
    else:
        form = TeacherSubjectAssignmentForm(school=school)

    return render(request, 'teachers/add_teacher_subject.html', {'form': form})
