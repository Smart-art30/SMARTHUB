from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from accounts.decorators import role_required
from schools.models import SchoolClass
from students.models import Student
from .models import Subject, Exam, StudentMark
from .forms import SubjectForm
from teachers.models import Teacher
from .models import Exam, ExamSubject, SchoolClass, Subject







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
    """
    View to create a new exam for all classes in the school,
    and link all subjects to each class via ExamSubject.
    """
    if request.method == 'POST':
        # Get data from the form
        name = request.POST.get('name', '').strip()
        term = request.POST.get('term', '').strip()
        year_str = request.POST.get('year', '').strip()

        # Validate inputs
        if not name or not term or not year_str:
            messages.error(request, "All fields are required.")
            return render(request, 'academics/exam_add.html')

        try:
            year = int(year_str)
        except ValueError:
            messages.error(request, "Year must be a valid number.")
            return render(request, 'academics/exam_add.html')

        # Fetch all classes and subjects for the school
        classes = SchoolClass.objects.filter(school=request.user.school)
        subjects = Subject.objects.filter(school=request.user.school)

        if not classes.exists():
            messages.error(request, "No classes found for your school.")
            return render(request, 'academics/exam_add.html')

        if not subjects.exists():
            messages.error(request, "No subjects found for your school.")
            return render(request, 'academics/exam_add.html')

      
        exams_created = 0
        exam_subjects_created = 0

        for cls in classes:
            
            exam, created = Exam.objects.get_or_create(
                name=name,
                term=term,
                year=year,
                school=request.user.school,
                school_class=cls
            )
            if created:
                exams_created += 1

            for subj in subjects:
                _, es_created = ExamSubject.objects.get_or_create(
                    exam=exam,
                    school_class=cls,
                    subject=subj
                )
                if es_created:
                    exam_subjects_created += 1

        messages.success(
            request,
            f"Exams created: {exams_created}, ExamSubjects created: {exam_subjects_created}."
        )
        return redirect('academics:exam_list')

    return render(request, 'academics/exam_add.html')



@login_required
@role_required('schooladmin')
def exam_subject_add(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id, school=request.user.school)
    classes = SchoolClass.objects.filter(school=request.user.school)
    subjects = Subject.objects.filter(school=request.user.school)

    if request.method == 'POST':
        
        for cls in classes:
            subject_ids = request.POST.getlist(f'class_{cls.id}_subjects')
            for subj_id in subject_ids:
                subj = Subject.objects.get(id=subj_id, school=request.user.school)
                
                ExamSubject.objects.get_or_create(
                    exam=exam,
                    subject=subj,
                    school_class=cls
                )

        messages.success(request, "ExamSubjects assigned successfully.")
        return redirect('exam_list')

    return render(request, 'academics/exam_subject_add.html', {
        'exam': exam,
        'classes': classes,
        'subjects': subjects
    })






@login_required
@role_required('teacher')
def select_class(request):
    teacher = get_object_or_404(Teacher, user=request.user)

    classes = (
        SchoolClass.objects
        .filter(
            teacherclass__teacher=teacher,
            school=teacher.school
        )
        .distinct()
        .order_by('name', 'stream')
    )

    return render(request, 'academics/select_class.html', {
        'classes': classes
    })


@login_required
@role_required('teacher')
def class_overview(request, class_id):
    teacher = get_object_or_404(Teacher, user=request.user)

    school_class = get_object_or_404(
        SchoolClass,
        id=class_id,
        school=teacher.school
    )


    students = Student.objects.filter(student_class=school_class)

    
    subjects = Subject.objects.filter(
        teachersubjectassignment__school_class=school_class,
        teachersubjectassignment__teacher=teacher
    ).distinct()

    return render(request, 'academics/class_overview.html', {
        'school_class': school_class,
        'students': students,
        'subjects': subjects
    })



@login_required
@role_required('teacher')
def select_exam(request, class_id, subject_id):
    teacher = get_object_or_404(Teacher, user=request.user)

    school_class = get_object_or_404(
        SchoolClass,
        id=class_id,
        school=teacher.school
    )

    subject = get_object_or_404(Subject, id=subject_id)

   
    exams = Exam.objects.filter(
        school=teacher.school,
        school_class=school_class,
        subject=subject
    )

    return render(request, 'academics/select_exam.html', {
        'school_class': school_class,
        'subject': subject,
        'exams': exams
    })

@login_required
@role_required('teacher')
def enter_marks(request, exam_id):
    exam = get_object_or_404(
        Exam,
        id=exam_id,
        school=request.user.school
    )

    students = Student.objects.filter(
        school_class=exam.school_class
    )

    if request.method == 'POST':
        for student in students:
            marks = request.POST.get(f'marks_{student.id}')
            if marks != '':
                StudentMark.objects.update_or_create(
                    student=student,
                    exam=exam,
                    defaults={'marks': marks}
                )

        messages.success(request, "Marks saved successfully.")
        return redirect('class_overview', class_id=exam.school_class.id)

    existing_marks = {
        m.student_id: m.marks
        for m in StudentMark.objects.filter(exam=exam)
    }

    return render(request, 'academics/enter_marks.html', {
        'exam': exam,
        'students': students,
        'existing_marks': existing_marks
    })



@login_required
def student_report(request, student_id, exam_id):
    student = get_object_or_404(Student, id=student_id)
    exam = get_object_or_404(Exam, id=exam_id)

    marks = StudentMark.objects.filter(student=student, exam=exam)

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

