from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.http import Http404
from django.db import transaction

from accounts.decorators import role_required

from teachers.models import (
    Teacher,
    TeacherClass,
    TeacherSubjectAssignment,
)

from schools.models import SchoolClass
from students.models import Student

from .models import (
    Subject,
    Exam,
    ExamSubject,
    StudentMark,
)

from .forms import SubjectForm

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.db import transaction
import json




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
    """
    View to select an exam for a given class and subject.
    """
    school_class = get_object_or_404(SchoolClass, id=class_id)
    subject = get_object_or_404(Subject, id=subject_id)

    # Fetch exams for this class that include this subject
    exam_subjects = ExamSubject.objects.filter(
        school_class=school_class,
        subject=subject
    ).select_related('exam')

    if not exam_subjects.exists():
        return render(request, 'academics/no_exam.html', {
            'school_class': school_class,
            'subject': subject
        })

    return render(request, 'academics/select_exam.html', {
        'school_class': school_class,
        'subject': subject,
        'exam_subjects': exam_subjects
    })

@login_required
@role_required('teacher')
def enter_marks(request, class_id, exam_id):
    teacher = request.user
    exam = get_object_or_404(
        Exam,
        id=exam_id,
        school_class__id=class_id,
        school_class__school=teacher.teacher.school
    )

    students = Student.objects.filter(
        student_class__id=class_id
    ).order_by('user__last_name', 'user__first_name')

    subjects = Subject.objects.filter(
        examsubject__exam=exam,
        examsubject__school_class=exam.school_class
    ).distinct()

    existing_marks = {}
    marks_qs = StudentMark.objects.filter(exam=exam)
    for m in marks_qs:
        existing_marks.setdefault(m.student_id, {})[m.subject_id] = m.marks

    for student in students:
        student.marks_list = []
        total = 0
        for subject in subjects:
            mark_val = existing_marks.get(student.id, {}).get(subject.id, '')
            grade = ''
            if mark_val != '':
                temp_mark = StudentMark(student=student, exam=exam, subject=subject, marks=mark_val)
                grade = temp_mark.grade()
                total += float(mark_val)
            student.marks_list.append({
                'subject': subject,
                'mark': mark_val,
                'grade': grade
            })
        student.total = total
        student.average = round(total / len(subjects), 2) if subjects else 0

    if request.method == 'POST':
        with transaction.atomic():
            for student in students:
                for subject in subjects:
                    mark_value = request.POST.get(f'marks_{student.id}_{subject.id}', '').strip()
                    if mark_value:
                        try:
                            mark_float = float(mark_value)
                            mark_float = max(0, min(mark_float, exam.max_mark))
                        except ValueError:
                            mark_float = 0

                        StudentMark.objects.update_or_create(
                            student=student,
                            exam=exam,
                            subject=subject,
                            defaults={'marks': mark_float}
                        )
        messages.success(request, "Marks saved successfully.")
        return redirect('academics:class_overview', class_id=class_id)

   
    school_logo_url = teacher.teacher.school.logo.url if teacher.teacher.school.logo else None

    return render(request, 'academics/enter_marks.html', {
        'exam': exam,
        'students': students,
        'subjects': subjects,
        'school_logo_url': school_logo_url,  
    })



@login_required
@role_required('teacher')
@csrf_exempt  
def save_mark_ajax(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            student_id = int(data.get('student_id'))
            subject_id = int(data.get('subject_id'))
            exam_id = int(data.get('exam_id'))
            mark_value = data.get('mark', '').strip()

           
            if mark_value == '':
                mark_float = None
            else:
                try:
                    mark_float = float(mark_value)
                except ValueError:
                    return JsonResponse({'status':'error','message':'Invalid mark'})

            
            from academics.models import Student, Subject, Exam, StudentMark
            student = Student.objects.get(id=student_id)
            subject = Subject.objects.get(id=subject_id)
            exam = Exam.objects.get(id=exam_id)

            
            if mark_float is not None:
                mark_float = max(0, min(mark_float, exam.max_mark))

           
            with transaction.atomic():
                if mark_float is None:
                    
                    StudentMark.objects.filter(student=student, subject=subject, exam=exam).delete()
                else:
                    StudentMark.objects.update_or_create(
                        student=student,
                        subject=subject,
                        exam=exam,
                        defaults={'marks': mark_float}
                    )

            return JsonResponse({'status':'ok'})

        except Exception as e:
            return JsonResponse({'status':'error', 'message': str(e)})
    
    return JsonResponse({'status':'error', 'message':'Invalid request method'})


@login_required
def student_report(request, student_id):
    student = get_object_or_404(Student, id=student_id)

    # Subjects assigned to this class
    subjects = Subject.objects.filter(
        teachersubjectassignment__school_class=student.student_class
    ).distinct().order_by('name')

    # Exams in class, ordered by term
    all_exams = list(Exam.objects.filter(school_class=student.student_class))
    exam_order = ['Opener', 'Mid-term', 'End-term']
    exams = sorted(all_exams, key=lambda x: exam_order.index(x.term) if x.term in exam_order else 99)

    # Build report rows
    report_rows_with_trends = []
    exam_totals = [0] * len(exams)
    exam_counts = [0] * len(exams)

    # Collect facilitators per subject (from marks)
    subject_facilitators = {}

    for subject in subjects:
        marks_with_trends = []
        total_marks = 0
        count_marks = 0

        marks_list = []
        for exam in exams:
            mark_obj = StudentMark.objects.filter(student=student, subject=subject, exam=exam).first()
            marks_list.append(mark_obj.marks if mark_obj else 0)

            # Save facilitator for this subject if available
            if mark_obj and mark_obj.facilitator:
                subject_facilitators[subject.name] = mark_obj.facilitator.get_full_name()

        for idx, mark in enumerate(marks_list):
            if idx == 0:
                trend = 'same'
            else:
                prev_mark = marks_list[idx - 1]
                trend = 'up' if mark > prev_mark else 'down' if mark < prev_mark else 'same'
            marks_with_trends.append({'mark': mark, 'trend': trend})

            total_marks += mark
            if mark != 0:
                count_marks += 1

            exam_totals[idx] += mark
            if mark != 0:
                exam_counts[idx] += 1

        # Subject remark
        avg_subject = total_marks / count_marks if count_marks else 0
        if avg_subject >= 80:
            remark = 'Exceeding Expectation'
        elif avg_subject >= 60:
            remark = 'Meeting Expectation'
        elif avg_subject >= 40:
            remark = 'Approaching Expectation'
        else:
            remark = 'Below Expectation'

        report_rows_with_trends.append({
            'subject': subject.name,
            'marks': marks_with_trends,
            'remarks': remark
        })

    # Exam averages
    exam_averages = [round(exam_totals[i] / exam_counts[i], 2) if exam_counts[i] else 0 for i in range(len(exams))]

    # Facilitator – pull the first available from marks, fallback to N/A
    first_facilitator = StudentMark.objects.filter(student=student, facilitator__isnull=False).first()
    facilitator = first_facilitator.facilitator.get_full_name() if first_facilitator else "N/A"

    # Class ranks
    class_students = Student.objects.filter(student_class=student.student_class)
    student_totals = []
    for s in class_students:
        total = sum(
            StudentMark.objects.filter(student=s, subject=subject, exam=exam).first().marks
            if StudentMark.objects.filter(student=s, subject=subject, exam=exam).exists() else 0
            for subject in subjects for exam in exams
        )
        student_totals.append({'student': s, 'total': total})

    sorted_totals = sorted(student_totals, key=lambda x: x['total'], reverse=True)
    for idx, entry in enumerate(sorted_totals, start=1):
        entry['rank'] = idx

    student_rank = next((entry['rank'] for entry in sorted_totals if entry['student'] == student), None)

    return render(request, 'academics/student_report.html', {
        'student': student,
        'exams': exams,
        'report_rows_with_trends': report_rows_with_trends,
        'exam_totals': exam_totals,
        'exam_averages': exam_averages,
        'facilitator': facilitator, 
        'subject_facilitators': subject_facilitators,  # Optional per-subject
        'student_rank': student_rank,
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
