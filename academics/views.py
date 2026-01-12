from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from accounts.decorators import role_required
from .models import Subject, Exam, StudentMark
from schools.models import SchoolClass
from students.models import Student

@login_required
@role_required('schooladmin')
def subject_list(request):
    subjects = Subject.objects.filter(school=request.user.school)
    return render(request, 'academics/subjects_list.html', {'subjects': subjects})

@login_required
@role_required('schooladmin')
def subject_add(request):
    if request.method == 'POST':
        name = request.POST.get('name')
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
def exam_add(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        term = request.POST.get('term')
        Exam.objects.create(
            name=name,
            term=term,
            school=request.user.school
        )
        return redirect('exam_list')
    return render(request, 'academics/exam_add.html')

@login_required
@role_required('schooladmin')
def mark_entry(request):
    students = Student.objects.filter(school=request.user.school)
    exams = Exam.objects.filter(school=request.user.school)
    subjects = Subject.objects.filter(school=request.user.school)

    if request.method == 'POST':
        student_id = request.POST.get('student')
        exam_subject_id = request.POST.get('exam_subject')
        marks_value = request.POST.get('marks')

        StudentMark.objects.create(
            student_id=student_id,
            exam_subject_id=exam_subject_id,
            marks=marks_value
        )

        return redirect('mark_entry')

    return render(request, 'academics/mark_entry.html', {
        'students': students,
        'exams': exams,
        'subjects': subjects,
    })

@login_required
def student_report(request, student_id, exam_id):
    student = get_object_or_404(Student, id=student_id)
    exam = get_object_or_404(Exam, id=exam_id)

    exam_subjects = exam.examsubject_set.all()
    marks = StudentMark.objects.filter(student=student, exam_subject__in=exam_subjects)

    total = sum(m.marks for m in marks)
    average = total / marks.count() if marks.exists() else 0

    return render(request, 'academics/student_report.html', {
        'student': student,
        'exam': exam,
        'marks': marks,
        'total': total,
        'average': average,
    })

@login_required
@role_required('schooladmin')
def report_list(request):
    students = Student.objects.filter(school=request.user.school)
    exams = Exam.objects.filter(school=request.user.school)
    return render(request, 'academics/report_list.html', {
        'students': students,
        'exams': exams,
    })
