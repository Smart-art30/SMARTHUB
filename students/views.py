from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.auth.decorators import login_required
from accounts.decorators import role_required
from .models import Student
from schools.models import SchoolClass

@login_required
@role_required('schooladmin')
def student_list(request):
    students = Student.objects.filter(school=request.user.school)
    return render(request, 'students/students_list.html',{'students':students} )


@login_required
@role_required('schooladmin')
def student_add(request):
    classes = SchoolClass.objects.filter(school=request.user.school) 

    if request.method == 'POST':
        user_id  = request.POST.get('user')
        admission = request.Post.get('admission_number')
        class_id = request.POST.get('student_class')

        student.objects.create(
            user_id=user_id,
            school = request.user.school,
            admission_number=admission,
            student_class_id = class_id
        )
        return redirect('student_list')
    return render(request, 'students/student_add.html',{'classes':classes})

@login_required
def student_detail(request, pk):
    student= get_object_or_404(Student, pk=pk)

    return render(request, 'students/student_detail.html', {'student':student})