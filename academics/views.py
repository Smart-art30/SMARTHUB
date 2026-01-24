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
from teachers.models import TeacherSubjectAssignment
from schools.models import SchoolClass
from teachers.models import TeacherClass







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
def select_class(request, class_id):
    teacher = request.user.teacher

    selected_class = get_object_or_404(
        SchoolClass.objects.filter(
            teachersubjectassignment__teacher=teacher
        ).distinct(),
        id=class_id
    )

    assignments = TeacherSubjectAssignment.objects.filter(
        teacher=teacher,
        school_class=selected_class
    ).select_related('subject')

    return render(request, 'academics/select_class.html', {
        'school_class': selected_class,
        'assignments': assignments,
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

   
    exam_subject = get_object_or_404(
        ExamSubject,
        school_class=school_class,
        subject=subject
    )

    exams = Exam.objects.filter(
        school=teacher.school,
        school_class=school_class,
        examsubject=exam_subject
    )

    return render(request, 'academics/select_exam.html', {
        'school_class': school_class,
        'subject': subject,
        'exams': exams
    })

@login_required
@role_required('teacher')
def enter_marks(request, exam_id):
    teacher = request.user.teacher
    teacher_school = teacher.school

    exam = get_object_or_404(
        Exam,
        id=exam_id,
        school_class__school=teacher_school
    )

    students = Student.objects.filter(student_class=exam.school_class)
    subjects = exam.subjects.all()

    existing_marks = {}
    marks_qs = StudentMark.objects.filter(exam=exam)
    for m in marks_qs:
        existing_marks.setdefault(m.student_id, {})[m.subject_id] = m.marks

    if request.method == 'POST':
        for student in students:
            for subject in subjects:
                mark_value = request.POST.get(f'marks_{student.id}_{subject.id}')
                if mark_value != '':
                    StudentMark.objects.update_or_create(
                        student=student,
                        exam=exam,
                        subject=subject,
                        defaults={'marks': mark_value}
                    )
        messages.success(request, "Marks saved successfully.")
        return redirect('academics:class_overview', class_id=exam.school_class.id)

    
    for student in students:
        student.marks = {subject.id: existing_marks.get(student.id, {}).get(subject.id, '') for subject in subjects}
        student.total = sum([float(v) for v in student.marks.values() if v != ''])

    return render(request, 'academics/enter_marks.html', {
        'exam': exam,
        'students': students,
        'subjects': subjects,
    })




@login_required
def student_report(request, student_id, exam_id):
    student = get_object_or_404(Student, id=student_id)
    exam = get_object_or_404(Exam, id=exam_id)

    subjects = Subject.objects.filter(school=student.school)

    marks_list = []
    total = 0

    for subject in subjects:
        mark_obj = StudentMark.objects.filter(student=student, exam=exam, subject=subject).first()
        score = mark_obj.marks if mark_obj else 0
        total += score
        marks_list.append({'subject': subject, 'score': score})

    average = total / subjects.count() if subjects.exists() else 0

    return render(request, 'academics/student_report.html', {
        'student': student,
        'exam': exam,
        'marks': marks_list,
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

@login_required
@role_required('schooladmin')
def assign_teacher(request):
    if request.method == "POST":
        teacher = Teacher.objects.get(id=request.POST['teacher'])
        school_class = SchoolClass.objects.get(id=request.POST['school_class'])
        subject = Subject.objects.get(id=request.POST['subject'])

        obj, created = TeacherClass.objects.get_or_create(
            teacher=teacher,
            school_class=school_class,
            subject=subject
        )

        if created:
            messages.success(
                request, 
                f"{teacher.user.get_full_name()} assigned to {school_class.name} ({subject.name})"
            )
        else:
            messages.warning(request, "This assignment already exists.")

        return redirect('academics:assign_teacher')

    context = {
        'teachers': Teacher.objects.all(),
        'classes': SchoolClass.objects.all(),
        'subjects': Subject.objects.all(),
    }
    return render(request, 'academics/assign_teacher.html', context)



@login_required
@role_required('teacher')
def select_marks_classes(request):
    """
    Page for teacher to select one or more assigned classes
    before entering marks.
    """
    teacher = request.user.teacher
    classes = teacher.assigned_classes.all()

    if request.method == 'POST':
        class_ids = request.POST.getlist('classes')
        if class_ids:
            return redirect('academics:enter_marks_multi') + f"?classes={','.join(class_ids)}"

    return render(request, 'academics/select_classes.html', {
        'classes': classes
    })




@login_required
@role_required('teacher')
def enter_marks_multi(request):
    """
    Display students x subjects table for selected classes and exams.
    """
    teacher = request.user.teacher
    class_ids = request.GET.get('classes', '')
    class_ids = [int(cid) for cid in class_ids.split(',') if cid]

    selected_classes = SchoolClass.objects.filter(id__in=class_ids, teachers=teacher)

    # All students in selected classes
    students = Student.objects.filter(student_class__in=selected_classes).order_by('student_class__name', 'user__last_name')

    # Subjects for these classes assigned to this teacher
    subjects = Subject.objects.filter(teacher_assignments__teacher=teacher, teacher_assignments__school_class__in=selected_classes).distinct()

    # Get or create the latest exam for each subject+class
    exam_dict = {}
    for subject in subjects:
        for cls in selected_classes:
            exam, created = Exam.objects.get_or_create(
                school_class=cls,
                subject=subject,
                defaults={'name': f'{subject.name} Exam', 'term': 'Term 1', 'year': 2026, 'max_mark': 100}
            )
            exam_dict[(cls.id, subject.id)] = exam

    # Get existing marks
    existing_marks = StudentMark.objects.filter(
        student__in=students,
        exam__in=exam_dict.values()
    )
    marks_dict = {}
    for mark in existing_marks:
        marks_dict.setdefault(mark.student_id, {})[mark.exam.subject.id] = mark.marks

    if request.method == 'POST':
        for student in students:
            for subject in subjects:
                exam = exam_dict[(student.student_class.id, subject.id)]
                mark_value = request.POST.get(f'marks_{student.id}_{subject.id}')
                if mark_value != '':
                    StudentMark.objects.update_or_create(
                        student=student,
                        exam=exam,
                        subject=subject,
                        defaults={'marks': mark_value}
                    )
        messages.success(request, "Marks saved successfully!")
        return redirect('dashboard:teacher_dashboard')

    # Attach marks and total to each student
    for student in students:
        student.marks = {subject.id: marks_dict.get(student.id, {}).get(subject.id, '') for subject in subjects}
        student.total = sum([float(v) for v in student.marks.values() if v != ''])

    return render(request, 'academics/enter_marks_multi.html', {
        'students': students,
        'subjects': subjects,
        'selected_classes': selected_classes,
    })