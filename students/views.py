from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.auth.decorators import login_required
from accounts.decorators import role_required
from .models import Student
from schools.models import SchoolClass
from django.contrib.auth import get_user_model
from .forms import StudentAddForm


User = get_user_model()

@login_required
@role_required('schooladmin')
def student_list(request):
    students = Student.objects.filter(school=request.user.school)
    return render(request, 'students/students_list.html',{'students':students} )


@login_required
@role_required('schooladmin')
def student_add(request):
    school = request.user.school
    classes = SchoolClass.objects.filter(school=school)

    if request.method == 'POST':
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        username = request.POST['username']
        admission = request.POST['admission_number']
        class_id = request.POST['student_class']

        # 🔒 Create student user
        user = User.objects.create_user(
            username=username,
            first_name=first_name,
            last_name=last_name,
            role='student',
            school=school,
            password=User.objects.make_random_password()
        )

        # 🔒 Create student profile
        Student.objects.create(
            user=user,
            school=school,
            admission_number=admission,
            student_class_id=class_id
        )

        return redirect('student_list')

    return render(request, 'students/student_add.html', {
        'classes': classes
    })
@login_required
def student_detail(request, pk):
    student= get_object_or_404(Student, pk=pk)

    return render(request, 'students/student_detail.html', {'student':student})