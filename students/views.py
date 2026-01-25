from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.auth.decorators import login_required
from accounts.decorators import role_required
from .models import Student, Parent
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
    classes = SchoolClass.objects.filter(
        school=request.user.school
    ).prefetch_related('student_set')

    return render(
        request,
        'students/students_list.html',
        {'classes': classes}
    )


@login_required
@role_required('schooladmin')
def student_add(request):
    school = request.user.school 
    classes = SchoolClass.objects.filter(school=school)  

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
            return redirect('students:student_add')

        if Student.objects.filter(admission_number=admission, school=school).exists():
            messages.error(request, f"Admission number {admission} already exists in this school.")
            return redirect('students:student_add')

    
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
            return redirect('students:student_add')

        messages.success(request, f"Student added successfully. Temporary password: {password}")
        return redirect('students:student_list')

    return render(request, 'students/student_add.html', {'classes': classes})


@login_required
def student_detail(request, pk):
    student= get_object_or_404(Student, pk=pk)

    return render(request, 'students/student_detail.html', {'student':student})

@login_required
@role_required('schooladmin')

def parent_list(request):
    school = request.user.school
    parents  = Parent.objects.filter(school=school)

    return render(request, 'students/parent_list.html', {
        'parents': parents
    })


@login_required
@role_required('schooladmin')
def add_parent(request):
    school = request.user.school
    students = Student.objects.filter(school=school)  

    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        student_ids = request.POST.getlist('students')

       
        if User.objects.filter(username=email).exists():
            messages.error(request, f'A user with this email: "{email}" already exists.')
            return redirect('students:add_parent')  

        password = secrets.token_urlsafe(8)

        user = User.objects.create_user(
            username=email,
            email=email,
            first_name=first_name,
            last_name=last_name,
            password=password
        )
        user.role = 'parent'
        user.school = school
        user.save()

        parent = Parent.objects.create(
            user=user,
            school=school,
            phone=phone,
            address=address
        )

     
        if student_ids:
            parent.students.set(student_ids)

        messages.success(request, f'Parent added successfully. Temporary password: {password}')
        return redirect('students/parent_list')

    
    return render(request, 'students/add_parent.html', {
        'students': students 
    })
