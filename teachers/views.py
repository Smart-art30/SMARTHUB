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
from .forms import TeacherSubjectAssignmentForm,TeacherAdminForm
from .models import TeacherSubjectAssignment
from schools.models import SchoolClass
from academics.models import Subject
from collections import defaultdict 
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.template.loader import render_to_string





User = get_user_model()

@login_required
@role_required('schooladmin')
def teacher_list(request):
    teachers = Teacher.objects.filter(school=request.user.school)
    return render(request, 'teachers/teacher_list.html', {'teachers': teachers})



def generate_random_password(length=10):
    alphabet = string.ascii_letters + string.digits + string.punctuation
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def generate_unique_username(email):
    base_username = email.split('@')[0]
    username = base_username
    counter = 1
    while User.objects.filter(username=username).exists():
        username = f"{base_username}{counter}"
        counter += 1
    return username



def generate_random_password(length=10):
    alphabet = string.ascii_letters + string.digits + string.punctuation
    return ''.join(secrets.choice(alphabet) for _ in range(length))



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
        form = TeacherProfileForm(request.POST, request.FILES, instance=teacher)
        if form.is_valid():
            form.save()
           
            return redirect('dashboard:teacher_dashboard')
    else:
        form = TeacherProfileForm(instance=teacher)

    return render(request, 'teachers/teacher_profile_edit.html', {
        'form': form,
        'teacher': teacher
    })


@login_required
@role_required('schooladmin')

def assign_teacher_subjects(request):
    teachers = Teacher.objects.select_related('user').all()
    classes = SchoolClass.objects.all()
    subjects = Subject.objects.all()

    selected_teacher = None
    selected_class = None
    assigned_subject_ids = []

    teacher_id = request.POST.get('teacher') or request.GET.get('teacher')
    class_id = request.POST.get('school_class') or request.GET.get('school_class')

    if teacher_id and class_id:
        selected_teacher = get_object_or_404(Teacher, id=teacher_id)
        selected_class = get_object_or_404(SchoolClass, id=class_id)

        assigned_subject_ids = list(
            TeacherSubjectAssignment.objects.filter(
                teacher=selected_teacher,
                school_class=selected_class
            ).values_list('subject_id', flat=True)
        )

    # Handle POST
    if request.method == 'POST' and selected_teacher and selected_class:
        subject_ids = request.POST.getlist('subjects')
        selected_subjects = Subject.objects.filter(id__in=subject_ids)

        # Remove unchecked
        TeacherSubjectAssignment.objects.filter(
            teacher=selected_teacher,
            school_class=selected_class
        ).exclude(subject__in=selected_subjects).delete()

        # Add new
        for subject in selected_subjects:
            TeacherSubjectAssignment.objects.get_or_create(
                teacher=selected_teacher,
                school_class=selected_class,
                subject=subject
            )

        return redirect(f"{request.path}?teacher={selected_teacher.id}&school_class={selected_class.id}")

    # Group assignments by teacher -> class -> subjects
    teacher_data = defaultdict(list)  # key=teacher, value=list of dicts {class, subjects}
    all_assignments = TeacherSubjectAssignment.objects.select_related(
        'teacher', 'school_class', 'subject'
    ).order_by('teacher__user__first_name', 'school_class__name')

    for assign in all_assignments:
        # Check if this class already exists in teacher_data
        existing = next((x for x in teacher_data[assign.teacher] if x['class'] == assign.school_class), None)
        if existing:
            existing['subjects'].append(assign.subject)
        else:
            teacher_data[assign.teacher].append({
                'class': assign.school_class,
                'subjects': [assign.subject]
            })

    context = {
        'teachers': teachers,
        'classes': classes,
        'subjects': subjects,
        'selected_teacher': selected_teacher,
        'selected_class': selected_class,
        'assigned_subject_ids': assigned_subject_ids,
        'teacher_data': dict(teacher_data),
    }

    return render(request, 'teachers/assign_teacher_subject.html', context)

def remove_teacher_subjects(request, teacher_id, class_id):
    teacher = get_object_or_404(Teacher, id=teacher_id)
    school_class = get_object_or_404(SchoolClass, id=class_id)

    TeacherSubjectAssignment.objects.filter(
        teacher=teacher,
        school_class=school_class
    ).delete()

    return redirect(f"/teachers/assign/?teacher={teacher.id}&school_class={school_class.id}")


# Remove a single assignment
def remove_single_assignment(request, assignment_id):
    assignment = get_object_or_404(TeacherSubjectAssignment, id=assignment_id)
    teacher = assignment.teacher
    school_class = assignment.school_class
    assignment.delete()
    return redirect(f"/teachers/assign/?teacher={teacher.id}&school_class={school_class.id}")


@csrf_exempt  # Use only for AJAX POST; or use proper CSRF token in headers

def ajax_assign_subjects(request):
    if request.method == 'POST':
        teacher_id = request.POST.get('teacher')
        class_id = request.POST.get('school_class')
        subject_ids = request.POST.getlist('subjects[]')

        teacher = get_object_or_404(Teacher, id=teacher_id)
        school_class = get_object_or_404(SchoolClass, id=class_id)
        subjects = Subject.objects.filter(id__in=subject_ids)

        # Remove unchecked assignments
        TeacherSubjectAssignment.objects.filter(
            teacher=teacher,
            school_class=school_class
        ).exclude(subject__in=subjects).delete()

        # Add new assignments
        for subject in subjects:
            TeacherSubjectAssignment.objects.get_or_create(
                teacher=teacher,
                school_class=school_class,
                subject=subject
            )

        # Rebuild teacher_data for updated assignments
        teacher_data = {}  # same structure as in your main view
        assignments = TeacherSubjectAssignment.objects.select_related(
            'teacher', 'school_class', 'subject'
        ).all()

        from collections import defaultdict
        grouped = defaultdict(lambda: defaultdict(list))
        for a in assignments:
            grouped[a.teacher][a.school_class].append(a.subject)

        # Convert to list for template
        teacher_data = {}
        for teacher_obj, classes in grouped.items():
            class_list = []
            for class_obj, subjects in classes.items():
                class_list.append({'class': class_obj, 'subjects': subjects})
            teacher_data[teacher_obj] = class_list

        html_assignments = render_to_string(
            'teachers/partial_assignments.html',
            {'teacher_data': teacher_data}
        )

        return JsonResponse({'status': 'success', 'html_assignments': html_assignments})

    return JsonResponse({'status': 'error', 'message': 'Invalid request'})

@login_required
@role_required('schooladmin')
def teacher_edit(request, pk):
    teacher = get_object_or_404(Teacher, pk=pk)

    if request.method == 'POST':
        form = TeacherAdminForm(request.POST, request.FILES, instance=teacher)
        if form.is_valid():
            form.save()
            messages.success(request, 'Teacher updated successfully!')
            return redirect('teachers:teacher_detail', pk=teacher.pk)
    else:
        form = TeacherAdminForm(instance=teacher)

    return render(request, 'teachers/teacher_edit.html', {'form': form, 'teacher': teacher})


@login_required
@role_required('schooladmin')
def teacher_delete(request, pk):
    teacher = get_object_or_404(Teacher, pk=pk)
    if request.method == 'POST':
        
        user = teacher.user
        teacher.delete()
        user.delete()
        messages.success(request, 'Teacher deleted successfully!')
        return redirect('teachers:teacher_list')

  
    return render(request, 'teachers/teacher_confirm_delete.html', {'teacher': teacher})


@login_required
@role_required('schooladmin')
def assign_class_teacher(request, teacher_id):
    teacher = get_object_or_404(
        Teacher,
        id=teacher_id,
        school=request.user.school
    )

    classes = SchoolClass.objects.filter(
        school=request.user.school
    )

    if request.method == "POST":
        class_id = request.POST.get("school_class")
        school_class = get_object_or_404(
            SchoolClass,
            id=class_id,
            school=request.user.school
        )

        school_class.class_teacher = teacher
        school_class.save()

        messages.success(
            request,
            f"{teacher} is now the class teacher for {school_class}"
        )
        return redirect("teachers:teacher_list")

    return render(
        request,
        "teachers/assign_class_teacher.html",
        {
            "teacher": teacher,
            "classes": classes
        }
    )
