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
from django.urls import reverse


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
def subject_edit(request, pk):
    school = request.user.school
    subject = get_object_or_404(Subject, pk=pk, school=school)  

    if request.method == 'POST':
        form = SubjectForm(request.POST, instance=subject, school=school)
        if form.is_valid():
            form.save()
            return redirect('academics:subject_list')
    else:
        form = SubjectForm(instance=subject, school=school)

    return render(request, 'academics/subjects_add.html', {'form': form, 'edit': True})


@login_required
def subject_delete(request, pk):
    school = request.user.school
    subject = get_object_or_404(Subject, pk=pk, school=school)

    if request.method == 'POST':
        subject.delete()
        return redirect('academics:subject_list')

    return render(request, 'academics/subject_confirm_delete.html', {'subject': subject})



@login_required
@role_required('schooladmin')
def exam_list(request):
    exams = (
        Exam.objects
        .filter(school=request.user.school)
        .values('name', 'term', 'year')
        .distinct()
        .order_by('-year', 'term', 'name')
    )
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

    # --- Fetch ExamSubjects safely ---
    exam_subjects = ExamSubject.objects.filter(
        school_class=school_class,
        subject=subject
    )

    if not exam_subjects.exists():
        raise Http404("No exam found for this class and subject")

   
    exam_subject = exam_subjects.first()

    # --- Fetch related exams ---
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

    # Fetch the exam safely
    exam = get_object_or_404(
        Exam,
        id=exam_id,
        school_class__school=teacher_school
    )

    # Fetch students in the class
    students = Student.objects.filter(
        student_class=exam.school_class
    ).order_by('user__last_name', 'user__first_name')

    # Subjects assigned to this teacher for the class
    subjects = Subject.objects.filter(
        teachersubjectassignment__teacher=teacher,
        teachersubjectassignment__school_class=exam.school_class
    ).distinct()

    # Get existing marks as a dict: student_id -> {subject_id: mark}
    existing_marks = {}
    marks_qs = StudentMark.objects.filter(exam=exam)
    for m in marks_qs:
        existing_marks.setdefault(m.student_id, {})[m.subject_id] = m.marks

    # Prepare marks list per student
    for student in students:
        student.marks_list = []
        total = 0
        for subject in subjects:
            mark = existing_marks.get(student.id, {}).get(subject.id, '')
            student.marks_list.append({'subject': subject, 'mark': mark})
            if mark != '':
                total += float(mark)
        student.total = total
        student.average = total / len(subjects) if subjects else 0

    # Save marks
    if request.method == 'POST':
        for student in students:
            for subject in subjects:
                mark_value = request.POST.get(f'marks_{student.id}_{subject.id}', '').strip()
                if mark_value:
                    try:
                        mark_float = float(mark_value)
                    except ValueError:
                        mark_float = 0

                    # Safe update_or_create
                    StudentMark.objects.update_or_create(
                        student=student,
                        exam=exam,
                        subject=subject,  # include subject to satisfy NOT NULL
                        defaults={'marks': mark_float}
                    )

        messages.success(request, "Marks saved successfully.")
        return redirect('academics:class_overview', class_id=exam.school_class.id)

    return render(request, 'academics/enter_marks.html', {
        'exam': exam,
        'students': students,
        'subjects': subjects,
    })

@login_required
def student_report(request, student_id):
    student = get_object_or_404(Student, id=student_id)

    
    subjects = Subject.objects.filter(
        teachersubjectassignment__school_class=student.student_class
    ).distinct().order_by('name')

   
    exams = Exam.objects.filter(
        school_class=student.student_class
    ).order_by('name')

    
    marks_list = []
    total = 0

    for subject in subjects:
       
        marks_qs = StudentMark.objects.filter(
            student=student,
            subject=subject,
            exam__in=exams
        )

        subject_total = sum([m.marks for m in marks_qs])
        total += subject_total

        marks_list.append({
            'subject': subject,
            'score': subject_total
        })

    average = total / len(marks_list) if marks_list else 0

    report_data = [{
        'marks': marks_list,
        'total': total,
        'average': average,
    }]

    return render(request, 'academics/student_report.html', {
        'student': student,
        'report_data': report_data,
    })




@login_required
@role_required('schooladmin')
def report_list(request):
    classes = SchoolClass.objects.filter(
        school=request.user.school
    ).prefetch_related('student_set')

    exams = Exam.objects.filter(school=request.user.school)

    return render(
        request,
        'academics/report_list.html',
        {
            'classes': classes,
            'exams': exams,
        }
    )



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
    teacher = request.user.teacher

    assignments = TeacherClass.objects.filter(teacher=teacher)

  
    classes = SchoolClass.objects.filter(
        id__in=assignments.values_list('school_class_id', flat=True)
    ).distinct()

    if request.method == 'POST':
        class_ids = request.POST.getlist('classes')
        if class_ids:
            url = reverse('academics:enter_marks_multi')
            return redirect(f"{url}?classes={','.join(class_ids)}")

    return render(request, 'academics/select_classes.html', {
        'classes': classes
    })


@login_required
@role_required('teacher')
def enter_marks_multi(request):
    teacher = request.user.teacher

    # ---- GET SELECTED CLASSES ----
    class_ids = request.GET.get('classes', '')
    class_ids = [int(cid) for cid in class_ids.split(',') if cid]

    teacher_classes = TeacherClass.objects.filter(
        teacher=teacher,
        school_class_id__in=class_ids
    )

    selected_classes = SchoolClass.objects.filter(
        id__in=teacher_classes.values_list('school_class_id', flat=True)
    ).distinct()

    if not selected_classes.exists():
        return HttpResponseForbidden("You are not assigned to these classes.")

    # ---- STUDENTS ----
    students = Student.objects.filter(
        student_class__in=selected_classes
    ).select_related('student_class', 'user').order_by(
        'student_class__name', 'user__last_name'
    )

    # ---- SUBJECTS PER CLASS ----
    class_subjects = {}
    for cls in selected_classes:
        class_subjects[cls.id] = Subject.objects.filter(
            teachersubjectassignment__teacher=teacher,
            teachersubjectassignment__school_class=cls
        ).distinct()

    # Prepare list of tuples (class, subjects) for template
    classes_with_subjects = []
    for cls in selected_classes:
        subjects = class_subjects.get(cls.id, [])
        classes_with_subjects.append((cls, subjects))

    # ---- EXAMS PER CLASS & SUBJECT ----
    exam_dict = {}
    for cls, subjects in classes_with_subjects:
        for subject in subjects:
            exam, _ = Exam.objects.get_or_create(
                school=cls.school,
                school_class=cls,
                term='Term 1',  # adjust dynamically if needed
                year=2026,      # adjust dynamically if needed
                name=f'{subject.name} Exam',
                defaults={'max_mark': 100}
            )
            exam_dict[(cls.id, subject.id)] = exam

    # ---- EXISTING MARKS ----
    existing_marks = StudentMark.objects.filter(
        student__in=students,
        exam__in=exam_dict.values()
    ).select_related('student', 'exam', 'subject')

    # ---- PREPARE MARKS LIST PER STUDENT ----
    for student in students:
        student.marks_list = []
        total = 0
        student_subjects = class_subjects.get(student.student_class.id, [])

        for subject in student_subjects:
            # Only subjects assigned to this teacher
            if not TeacherSubjectAssignment.objects.filter(
                teacher=teacher,
                school_class=student.student_class,
                subject=subject
            ).exists():
                continue

            exam = exam_dict.get((student.student_class.id, subject.id))
            mark_obj = existing_marks.filter(
                student=student,
                exam=exam,
                subject=subject  # match by subject too
            ).first()

            mark_value = mark_obj.marks if mark_obj else ''
            student.marks_list.append({
                'subject': subject,
                'mark': mark_value
            })

            if mark_value != '':
                total += float(mark_value)

        student.total = total

    # ---- SAVE MARKS ----
    if request.method == 'POST':
        for student in students:
            for item in student.marks_list:
                subject = item['subject']
                exam = exam_dict.get((student.student_class.id, subject.id))
                if not exam:
                    continue

                mark_value = request.POST.get(f'marks_{student.id}_{subject.id}', '').strip()
                if mark_value:
                    try:
                        mark_float = float(mark_value)
                    except ValueError:
                        mark_float = 0

                    # Include subject to satisfy NOT NULL constraint
                    StudentMark.objects.update_or_create(
                        student=student,
                        exam=exam,
                        subject=subject,   # <--- FIXED HERE
                        defaults={'marks': mark_float}
                    )

        messages.success(request, "Marks saved successfully!")
        return redirect('dashboard:teacher_dashboard')

    # ---- RENDER ----
    return render(request, 'academics/enter_marks_multi.html', {
        'students': students,
        'classes_with_subjects': classes_with_subjects,  
    })





@login_required
@role_required('teacher')
def consolidated_student_report(request):
    teacher = request.user.teacher

    
    assignments = TeacherClass.objects.filter(teacher=teacher)
    classes = SchoolClass.objects.filter(
        id__in=assignments.values_list('school_class_id', flat=True)
    ).distinct()

    if not classes.exists():
        return HttpResponseForbidden("You are not assigned to any classes.")

   
    students = Student.objects.filter(student_class__in=classes).order_by('student_class__name', 'user__last_name')

  
    subjects = Subject.objects.filter(
        teachersubjectassignment__teacher=teacher,
        teachersubjectassignment__school_class__in=classes
    ).distinct()

    
    exams = Exam.objects.filter(school_class__in=classes).order_by('school_class__name', 'name')

    
    report_data = []

    for student in students:
        student_data = {'student': student, 'exams': []}

        #
        student_exams = exams.filter(school_class=student.student_class)

        for exam in student_exams:
            marks_list = []
            total = 0

            
            student_subjects = subjects.filter(
                teachersubjectassignment__school_class=student.student_class
            )

            for subject in student_subjects:
                mark_obj = StudentMark.objects.filter(
                    student=student,
                    exam=exam,
                    subject=subject
                ).first()

                score = mark_obj.marks if mark_obj else 0
                total += score

                marks_list.append({'subject': subject, 'score': score})

            average = total / len(marks_list) if marks_list else 0

            student_data['exams'].append({
                'exam': exam,
                'marks': marks_list,
                'total': total,
                'average': average
            })

        report_data.append(student_data)

   
    return render(request, 'academics/consolidated_student_report.html', {
        'report_data': report_data,
        'subjects': subjects,
        'classes': classes,
    })


@login_required
@role_required('schooladmin')
def enter_marks_group(request, name, term, year):
    exams = Exam.objects.filter(
        school=request.user.school,
        name=name,
        term=term,
        year=year
    ).select_related('school_class')

    if not exams.exists():
        messages.error(request, "No exams found.")
        return redirect('academics:exam_list')

    return render(request, 'academics/enter_marks_group.html', {
        'exams': exams,
        'exam_name': name,
        'term': term,
        'year': year,
    })

@login_required
@role_required('schooladmin')
def exam_update_group(request, name, term, year):
    exams = Exam.objects.filter(
        school=request.user.school,
        name=name,
        term=term,
        year=year
    )

    if not exams.exists():
        messages.error(request, "Exam not found.")
        return redirect('academics:exam_list')

    if request.method == 'POST':
        new_name = request.POST.get('name', '').strip()
        new_term = request.POST.get('term', '').strip()
        new_year = request.POST.get('year', '').strip()

        if not new_name or not new_term or not new_year:
            messages.error(request, "All fields are required.")
            return redirect(
                'academics:exam_update_group',
                name=name,
                term=term,
                year=year
            )

        try:
            new_year = int(new_year)
        except ValueError:
            messages.error(request, "Year must be a number.")
            return redirect(
                'academics:exam_update_group',
                name=name,
                term=term,
                year=year
            )

        exams.update(
            name=new_name,
            term=new_term,
            year=new_year
        )

        messages.success(request, "Exam updated successfully.")
        return redirect('academics:exam_list')

    
    exam = exams.first()

    return render(request, 'academics/exam_update_group.html', {
        'exam': exam
    })


@login_required
@role_required('schooladmin')
def exam_delete_group(request, name, term, year):
    exams = Exam.objects.filter(
        school=request.user.school,
        name=name,
        term=term,
        year=year
    )

    if not exams.exists():
        messages.error(request, "Exam not found.")
        return redirect('academics:exam_list')

    if request.method == 'POST':
        exams.delete()
        messages.success(request, "Exam deleted successfully.")
        return redirect('academics:exam_list')

    return render(request, 'academics/exam_confirm_delete.html', {
        'name': name,
        'term': term,
        'year': year
    })
