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


# -----------------------------
# Add teacher view
# -----------------------------
@login_required
@role_required('schooladmin')
def teacher_add(request):
    temp_username = None
    temp_password = None
    teacher_email = None

    # Pre-fill form data
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
        # Get form data
        for field in form_data:
            form_data[field] = request.POST.get(field)

        first_name = form_data['first_name']
        last_name = form_data['last_name']
        email = form_data['email']
        employee_id = form_data['employee_id']
        phone = form_data['phone']
        designation = form_data['designation']
        qualification = form_data['qualification']
        specialization = form_data['specialization']
        date_of_birth = form_data['date_of_birth']
        gender = form_data['gender']
        profile_picture = request.FILES.get('profile_picture')

        # Validate required fields
        if not all([first_name, last_name, email, employee_id, gender]):
            messages.error(request, 'Please fill all required fields including gender.')
            return render(request, 'teachers/teacher_add.html', {'form_data': form_data})

        # Check if employee ID already exists
        if Teacher.objects.filter(employee_id=employee_id).exists():
            messages.error(request, f"A teacher with Employee ID '{employee_id}' already exists.")
            return render(request, 'teachers/teacher_add.html', {'form_data': form_data})

        # Generate username and password
        username = generate_unique_username(email)
        random_password = generate_random_password()

        try:
            user = User.objects.create(
                username=username,
                first_name=first_name,
                last_name=last_name,
                email=email,
                password=make_password(random_password),
                role='teacher'
            )
        except IntegrityError:
            messages.error(request, f"A user with username '{username}' already exists. Try a different email.")
            return render(request, 'teachers/teacher_add.html', {'form_data': form_data})

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

        # Pass credentials to template
        temp_username = username
        temp_password = random_password
        teacher_email = email

        messages.success(request, f'Teacher added! Temporary credentials displayed below.')
        return render(request, 'teachers/teacher_add.html', {
            'temp_username': temp_username,
            'temp_password': temp_password,
            'teacher_email': teacher_email,
            'form_data': form_data
        })

    return render(request, 'teachers/teacher_add.html', {'form_data': form_data})

# -----------------------------
# Teacher detail
# -----------------------------
@login_required
@role_required('schooladmin')
def teacher_detail(request, pk):
    teacher = get_object_or_404(Teacher, pk=pk)
    return render(request, 'teachers/teacher_detail.html', {'teacher': teacher})
