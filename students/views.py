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
import csv
from django.http import HttpResponse
from .models import SchoolClass





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
def class_list(request):
    classes = SchoolClass.objects.filter(
        school=request.user.school
    )

    return render(
        request,
        'students/class_list.html',
        {'classes': classes}
    )

@login_required
@role_required('schooladmin')
def class_detail(request, pk):
    school_class = get_object_or_404(
        SchoolClass,
        pk=pk,
        school=request.user.school
    )

    students = Student.objects.filter(
        student_class=school_class,
        school=request.user.school
    ).select_related('user')

    return render(
        request,
        'students/class_detail.html',
        {
            'class': school_class,
            'students': students
        }
    )


@login_required
@role_required('schooladmin')
def class_download(request, class_id):
    school_class = get_object_or_404(
        SchoolClass,
        pk=class_id,
        school=request.user.school
    )

    students = school_class.student_set.select_related('user')

    response = HttpResponse(
        content_type='text/csv',
        headers={
            'Content-Disposition':
            f'attachment; filename="{school_class.name}_students.csv"'
        },
    )

    writer = csv.writer(response)
    writer.writerow(['No', 'First Name', 'Last Name', 'Admission', 'DOB', 'Gender'])

    for i, s in enumerate(students, start=1):
        writer.writerow([
            i,
            s.user.first_name,
            s.user.last_name,
            s.admission_number,
            s.date_of_birth,
            s.gender
        ])

    return response

#===========================================================================#
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



def student_update(request, pk):
    student = get_object_or_404(Student, pk=pk)

    if request.method == 'POST':
        form = StudentAddForm(request.POST, request.FILES, instance=student)
        if form.is_valid():
            form.save()
            messages.success(request, 'Student updated successfully.')
            return redirect('students:student_detail', pk=student.pk)
    else:
        form = StudentAddForm(instance=student)

    return render(request, 'students/student_form.html', {
        'form': form,
        'student': student,
        'title': 'Edit Student'
    })


def student_delete(request, pk):
    student = get_object_or_404(Student, pk=pk)

    if request.method == 'POST':
        student.delete()
        messages.success(request, 'Student deleted successfully.')
        return redirect('students:student_list')

    return render(request, 'students/student_confirm_delete.html', {
        'student': student
    })



@login_required
def student_detail(request, pk):
    student= get_object_or_404(Student, pk=pk)

    return render(request, 'students/student_detail.html', {'student':student})



@login_required
@role_required('schooladmin')
def parent_list(request):
    school = request.user.school
    parents = Parent.objects.filter(school=school)

    return render(request, 'students:parent_list.html', {   
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
        return redirect('students:parent_list') 
        

    return render(request, 'students/add_parent.html', {
        'students': students
    })







def class_download(request, class_id):
    school_class = SchoolClass.objects.get(pk=class_id)
    students = school_class.student_set.all()

    response = HttpResponse(
        content_type='text/csv',
        headers={'Content-Disposition': f'attachment; filename="{school_class.name}_students.csv"'},
    )

    writer = csv.writer(response)
    writer.writerow(['No', 'First Name', 'Last Name', 'Admission', 'DOB', 'Gender'])

    for i, s in enumerate(students, start=1):
        writer.writerow([
            i,
            s.user.first_name,
            s.user.last_name,
            s.admission_number,
            s.date_of_birth,
            s.gender
        ])

    return response
