from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from accounts.decorators import role_required
from .models import Subject, Exam, StudentMark
from schools.models import SchoolClass
from students.models import Student
from .forms import SubjectForm
from .models import Subject 


@login_required
@role_required('schooladmin')
def subject_list(request):
    subjects = Subject.objects.filter(school=request.user.school).order_by('name')
    return render(request, 'academics/subjects_list.html', {'subjects': subjects})

@login_required
def subject_add(request):
    school = request.user.school 
    

    if request.method == 'POST':
        form = SubjectForm(request.POST, school=school)
        if form.is_valid():
            subject = form.save(commit=False)
            subject.school = school
            subject.save()
            return redirect('academics:subject_list')
    else:
        form = SubjectForm(school=school)

    return render(request, 'academics/subjects_add.html', {'form': form})

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
@role_required('teacher')
def mark_entry(request, exam_subject_id):
    exam_subject = get_object_or_404(
        ExamSubject,
        id=exam_subject_id,
        exam__school=request.user.school
    )

    students = Student.objects.filter(
        school_class=exam_subject.exam.school_class
    )

    if request.method == 'POST':
        for student in students:
            marks = request.POST.get(f'marks_{student.id}')

            if marks:
                StudentMark.objects.update_or_create(
                    student=student,
                    exam_subject=exam_subject,
                    defaults={'marks': marks}
                )

        messages.success(request, "Marks saved successfully.")
        return redirect('teacher_dashboard')

    existing_marks = {
        m.student_id: m.marks
        for m in StudentMark.objects.filter(exam_subject=exam_subject)
    }

    return render(request, 'academics/mark_entry.html', {
        'exam_subject': exam_subject,
        'students': students,
        'existing_marks': existing_marks
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
