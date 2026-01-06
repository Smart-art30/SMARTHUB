from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from accounts.decorators import  role_required
from .models import Subject,Exam,mark
from schools.models import SchoolClass
from students.models import Student

@login_required
@role_required('schooladmin')
def subject_list(request):
    subjects = Subject.objects.filter(school=request.user.school)
    return render(request, 'academics/subjects_list.html', {'subjects':subjects})

@login_required
@role_required('schooladmin')
def subject_add(request):
    if request.method =='POST':
        name=request.POST.get('name')
        code = request.POST.get('code')
        Subject.objects.create(name=name, code=code, school=request.user.school)
        return redirect('subject_list')
    return render(request, 'academics/subjects_add.html')

@login_required
@role_required('schooladmin')
def exam_list(request):
    exams = Exam.objects.filter(school=request.user.school)
    return render(request, 'academics/exam_list.html', {'exams': exams})

@login_required
@role_required('schooladmin')
def add_exam(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        term - request.POST.get('term')
        Exam.objects.create(
            name=name,
            term = term,
            school=request.user.school
        )
        return redirect('exam_list')
    return render(request,'academics/exam_add.html')

@login_required
@role_required('schooladmin')
def mark_entry(request):
    students = Student.objects.filter(school=request.user.school)
    exams = Exam.objects.filter(school=request.user.school)
    subjects= Subject.objects.filetr(school=request.user.school)

    if request.method == 'POST':
        student_id = request.POST.get('student')
        exam_id = request.POST.get('exam')
        subject_id = request.POST.get('subject')
        score = request.POST.get('score')

        Mark.objects.create(
            student_id=student_id,
            exam_id=exam_id,
            subject_id=subject_id,
            score=score
        )

        return redirect('mark_entry')
    return render(request, 'academics/mark_entry.html',{
        'students': students,
        'exams' : exams,
        'subjects': subjects
    } )

@login_required
def student_report(request, student_id, exam_id):
    student = get_object_or_404(Student, id=student_id)
    exam = get_object_or_404(Exam, id=exam_id)

    marks = Mark.objects.filter(student=student, exam=exam)
    total = sum(m.score for m in marks)

    average = total/marks.count() if marks.exists() else 0

    return render(request, 'academics/student_report.html', {
        'students': student,
        'exam': exam,
        'marks': marks,
        'total': total,
        'average': average
    })
