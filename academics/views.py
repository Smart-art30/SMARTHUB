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
from django.db import models
from schools.forms import AssignExamForm
from .forms import AssignSubjectsToExamForm

from django.contrib.auth import get_user_model

User = get_user_model() 


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
        .exclude(name__isnull=True)
        .exclude(name__exact='')
        .order_by('-year', 'term', 'name')
    )

    
    for exam in exams:
        exam.assigned_classes = (
            SchoolClass.objects.filter(
                examsubject__exam=exam
            ).distinct()
        )

   
    if request.method == 'POST':
        exam_id = request.POST.get('exam_id')
        exam = Exam.objects.get(id=exam_id)
        form = AssignExamForm(request.POST, user=request.user)
        if form.is_valid():
            classes = form.cleaned_data['classes']
            for school_class in classes:
                for subject in school_class.subjects.all():
                    ExamSubject.objects.get_or_create(
                        exam=exam,
                        school_class=school_class,
                        subject=subject
                    )
            return redirect('academics:exam_list')
    else:
        form = AssignExamForm(user=request.user)

    return render(request, 'academics/exam_list.html', {
        'exams': exams,
        'form': form
    })


@login_required
@role_required('schooladmin')
def exam_add(request):

    if request.method == 'POST':
      
        name = request.POST.get('name', '').strip()
        term = request.POST.get('term', '').strip()
        year_str = request.POST.get('year', '').strip()

      
        if not name or not term or not year_str:
            messages.error(request, "All fields are required.")
            return render(request, 'academics/exam_add.html')

        try:
            year = int(year_str)
        except ValueError:
            messages.error(request, "Year must be a valid number.")
            return render(request, 'academics/exam_add.html')

        
        exam, created = Exam.objects.get_or_create(
            name=name,
            term=term,
            year=year,
            school=request.user.school,
        )

        if created:
            messages.success(request, f"Exam '{exam.name}' created successfully!")
        else:
            messages.info(request, f"Exam '{exam.name}' already exists.")

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



def exam_edit(request, pk):
    exam = get_object_or_404(Exam, pk=pk)
    
   
    new_name = request.GET.get('name')
    new_term = request.GET.get('term')
    new_year = request.GET.get('year')

    if new_name:
        exam.name = new_name
    if new_term:
        exam.term = new_term
    if new_year:
        exam.year = new_year

    exam.save()
    return redirect('academics:exam_list')


def exam_delete(request, pk):
    exam = get_object_or_404(Exam, pk=pk)
    exam.delete()
    return redirect('academics:exam_list')


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
    teacher = request.user.teacher

   
    school_class = get_object_or_404(
        SchoolClass,
        id=class_id,
        school=teacher.school
    )

    subject = get_object_or_404(
        Subject,
        id=subject_id,
        school=teacher.school
    )

    is_assigned = TeacherSubjectAssignment.objects.filter(
        teacher=teacher,
        school_class=school_class,
        subject=subject
    ).exists()

    if not is_assigned:
      
        return render(request, 'academics/not_assigned.html', {
            'school_class': school_class,
            'subject': subject,
            'message': "You are not assigned to this subject for this class."
        })

    
    exam_subjects = ExamSubject.objects.filter(
        school_class=school_class,
        subject=subject,
        exam__school=teacher.school
    ).select_related('exam').order_by('-exam__year', '-exam__term')

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

    school_class = get_object_or_404(
        SchoolClass,
        id=class_id,
        school=teacher.teacher.school
    )

    exam = get_object_or_404(
        Exam,
        id=exam_id,
        school=teacher.teacher.school
    )

    exam_subjects = ExamSubject.objects.filter(
        exam=exam,
        school_class=school_class
    )

    if not exam_subjects.exists():
        raise Http404("This exam is not assigned to this class")

    students = Student.objects.filter(
        student_class=school_class
    ).order_by('user__last_name', 'user__first_name')

  
    subjects = Subject.objects.filter(
        examsubject__exam=exam,
        examsubject__school_class=school_class
    ).distinct()

    existing_marks = {}
    for m in StudentMark.objects.filter(
        exam=exam,
        school_class=school_class
    ):
        existing_marks.setdefault(m.student_id, {})[m.subject_id] = m.marks

    
    for student in students:
        student.marks_list = []
        total = 0

        for subject in subjects:
            mark_val = existing_marks.get(student.id, {}).get(subject.id, '')
            grade = ''

            if mark_val != '':
                temp = StudentMark(
                    student=student,
                    subject=subject,
                    exam=exam,
                    marks=mark_val
                )
                grade = temp.grade()
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
                    value = request.POST.get(
                        f'marks_{student.id}_{subject.id}', ''
                    ).strip()

                    if value:
                        try:
                            mark_float = float(value)
                            mark_float = max(0, min(mark_float, exam.max_mark))
                        except ValueError:
                            mark_float = 0

                        StudentMark.objects.update_or_create(
                            student=student,
                            subject=subject,
                            exam=exam,
                            defaults={
                                'marks': mark_float,
                                'school_class': school_class,
                                'term': exam.term,
                                'facilitator': teacher
                            }
                        )

        messages.success(request, "Marks saved successfully.")
        return redirect('academics:class_overview', class_id=class_id)

 
    school = teacher.teacher.school
    school_logo_url = school.logo.url if school.logo else None

    return render(request, 'academics/enter_marks.html', {
        'exam': exam,
        'school_class': school_class,
        'students': students,
        'subjects': subjects,
        'school_logo_url': school_logo_url,  
    })




@login_required
@role_required('teacher')
def save_mark_ajax(request):
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "Invalid request"}, status=400)

    try:
        data = json.loads(request.body)

        student_id = data.get("student_id")
        subject_id = data.get("subject_id")
        exam_id = data.get("exam_id")
        marks = data.get("mark") 

        marks = float(marks)

        student = Student.objects.get(id=student_id)
        exam = Exam.objects.get(id=exam_id)
        subject = Subject.objects.get(id=subject_id)

        StudentMark.objects.update_or_create(
            student=student,
            subject=subject,
            exam=exam,
            defaults={
                "marks": marks,
                "school_class": student.student_class,
                "term": exam.term,
                "facilitator": request.user
            }
        )

        return JsonResponse({"status": "ok"})

    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)



@login_required
def student_report(request, student_id):
    student = get_object_or_404(Student, id=student_id)

   
    subjects = Subject.objects.filter(
        teachersubjectassignment__school_class=student.student_class
    ).distinct().order_by('name')

    
    exams = Exam.objects.filter(
        examsubject__subject__in=subjects  
    ).distinct()

 
    exam_order = ['Opener', 'Mid-term', 'End-term']
    exams = list(exams)
    exams.sort(key=lambda x: exam_order.index(x.term) if x.term in exam_order else 99)

    marks_qs = StudentMark.objects.filter(
        student=student,
        subject__in=subjects,
        exam__in=exams
    )
   
    marks_by_exam_subject = {(m.exam_id, m.subject_id): m for m in marks_qs}

  
    report_rows_with_trends = []
    exam_totals = [0] * len(exams)
    exam_counts = [0] * len(exams)
    subject_facilitators = {}

  
    for subject in subjects:
        marks_list = []
        marks_with_trends = []
        total_marks = 0
        count_marks = 0

        for idx, exam in enumerate(exams):
            mark_obj = marks_by_exam_subject.get((exam.id, subject.id))
            mark = mark_obj.marks if mark_obj else 0
            marks_list.append(mark)

           
            if mark_obj and mark_obj.facilitator:
                subject_facilitators[subject.name] = mark_obj.facilitator.get_full_name()

           
            exam_totals[idx] += mark
            if mark:
                exam_counts[idx] += 1

            total_marks += mark
            if mark:
                count_marks += 1

        
        for idx, mark in enumerate(marks_list):
            if idx == 0:
                trend = 'same'
            else:
                prev_mark = marks_list[idx - 1]
                if mark > prev_mark:
                    trend = 'up'
                elif mark < prev_mark:
                    trend = 'down'
                else:
                    trend = 'same'

            marks_with_trends.append({
                'mark': mark,
                'trend': trend
            })

   
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

  
    exam_averages = [
        round(exam_totals[i] / exam_counts[i], 2) if exam_counts[i] else 0
        for i in range(len(exams))
    ]

    
    first_facilitator = StudentMark.objects.filter(
        student=student,
        facilitator__isnull=False
    ).first()
    facilitator = (
        first_facilitator.facilitator.get_full_name()
        if first_facilitator else "N/A"
    )


    class_students = Student.objects.filter(student_class=student.student_class)
    student_totals = []

    
    all_marks = StudentMark.objects.filter(
        student__in=class_students,
        subject__in=subjects,
        exam__in=exams
    )

   
    totals_by_student = {}
    for m in all_marks:
        totals_by_student[m.student_id] = totals_by_student.get(m.student_id, 0) + (m.marks or 0)

    for s in class_students:
        total = totals_by_student.get(s.id, 0)
        student_totals.append({
            'student': s,
            'total': total
        })

    student_totals.sort(key=lambda x: x['total'], reverse=True)

    for idx, entry in enumerate(student_totals, start=1):
        entry['rank'] = idx

    student_rank = next(
        (entry['rank'] for entry in student_totals if entry['student'] == student),
        None
    )

    return render(request, 'academics/student_report.html', {
        'student': student,
        'exams': exams,
        'report_rows_with_trends': report_rows_with_trends,
        'exam_totals': exam_totals,
        'exam_averages': exam_averages,
        'facilitator': facilitator,
        'subject_facilitators': subject_facilitators,
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

from .models import School  # make sure you import your School model

@login_required
@role_required('schooladmin', 'teacher')
def class_report(request, class_id):
    school_class = get_object_or_404(SchoolClass, id=class_id)
    school = School.objects.first()  # or however you identify your school
    students = Student.objects.filter(student_class=school_class)

    subjects = Subject.objects.filter(
        teachersubjectassignment__school_class=school_class
    ).distinct().order_by('name')

    # Get all exams sorted
    exam_order = ['Opener', 'Mid-term', 'End-term']
    exams = list(Exam.objects.filter(examsubject__subject__in=subjects).distinct())
    exams.sort(key=lambda x: exam_order.index(x.term) if x.term in exam_order else 99)

    all_marks_qs = StudentMark.objects.filter(
        student__in=students,
        subject__in=subjects,
        exam__in=exams
    )
    marks_by_student_subject_exam = {
        (m.student_id, m.subject_id, m.exam_id): m for m in all_marks_qs
    }

    all_student_reports = []
    class_exam_totals = [0] * len(exams)
    class_exam_counts = [0] * len(exams)

    for student in students:
        report_rows = []
        student_total = 0
        student_exam_totals = [0] * len(exams)
        student_exam_counts = [0] * len(exams)

        for subject in subjects:
            marks_with_trends = []
            marks_list = []

            for idx, exam in enumerate(exams):
                mark_obj = marks_by_student_subject_exam.get((student.id, subject.id, exam.id))
                mark = mark_obj.marks if mark_obj else 0
                marks_list.append(mark)

                student_exam_totals[idx] += mark
                student_exam_counts[idx] += 1
                class_exam_totals[idx] += mark
                class_exam_counts[idx] += 1

            # Trend arrows
            for idx, mark in enumerate(marks_list):
                if idx == 0:
                    trend = 'same'
                else:
                    prev_mark = marks_list[idx - 1]
                    trend = 'up' if mark > prev_mark else ('down' if mark < prev_mark else 'same')
                marks_with_trends.append({'mark': mark, 'trend': trend})

            # Subject remark
            avg_subject = sum(marks_list) / len(exams) if exams else 0
            if avg_subject >= 80:
                remark = 'Exceeding Expectation'
            elif avg_subject >= 60:
                remark = 'Meeting Expectation'
            elif avg_subject >= 40:
                remark = 'Approaching Expectation'
            else:
                remark = 'Below Expectation'

            report_rows.append({
                'subject': subject.name,
                'marks': marks_with_trends,
                'remarks': remark
            })

            student_total += sum(marks_list)

        # Facilitator
        first_facilitator = next(
            (m.facilitator for m in all_marks_qs.filter(student=student, facilitator__isnull=False)),
            None
        )
        facilitator_name = first_facilitator.get_full_name() if first_facilitator else "N/A"

        exam_averages = [
            round(student_exam_totals[i] / student_exam_counts[i], 2) if student_exam_counts[i] else 0
            for i in range(len(exams))
        ]

        all_student_reports.append({
            'student': student,
            'report_rows_with_trends': report_rows,
            'exam_totals': student_exam_totals,
            'exam_averages': exam_averages,
            'total': student_total,
            'facilitator': facilitator_name,
        })

    # Class grand total
    class_grand_total = sum(class_exam_totals)
    class_exam_averages = [
        round(class_exam_totals[i] / class_exam_counts[i], 2) if class_exam_counts[i] else 0
        for i in range(len(exams))
    ]

    # Compute class rank
    all_student_reports.sort(key=lambda x: x['total'], reverse=True)
    rank = 0
    prev_total = None
    for idx, report in enumerate(all_student_reports, start=1):
        if report['total'] != prev_total:
            rank = idx
            prev_total = report['total']
        report['rank'] = rank

    return render(request, 'academics/class_report.html', {
        'school_class': school_class,
        'school': school,  
        'exams': exams,
        'all_student_reports': all_student_reports,
        'class_exam_totals': class_exam_totals,
        'class_exam_averages': class_exam_averages,
        'class_grand_total': class_grand_total,
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
def select_classes(request):
    teacher = request.user.teacher
    classes = SchoolClass.objects.filter(
        teachersubjectassignment__teacher=teacher
    ).distinct()

    return render(request, 'academics/select_classes.html', {
        'classes': classes
    })

@login_required
@role_required("schooladmin")
def assign_subjects_to_exam(request):
    assigned_subjects = ExamSubject.objects.none()
    exam = None
    school_class = None

    if request.method == "POST":
        form = AssignSubjectsToExamForm(request.POST)

        if form.is_valid():
            exam = form.cleaned_data["exam"]
            school_class = form.cleaned_data["school_class"]
            subjects = form.cleaned_data["subjects"]

            for subject in subjects:
                ExamSubject.objects.get_or_create(
                    exam=exam,
                    school_class=school_class,
                    subject=subject,
                )

            messages.success(request, "Subjects assigned successfully.")

           
            return redirect(
                f"{request.path}?exam={exam.id}&class={school_class.id}"
            )

    else:
        form = AssignSubjectsToExamForm()
        exam_id = request.GET.get("exam")
        class_id = request.GET.get("class")

        if exam_id and class_id:
            exam = get_object_or_404(Exam, id=exam_id)
            school_class = get_object_or_404(SchoolClass, id=class_id)

            assigned_subjects = ExamSubject.objects.filter(
                exam=exam,
                school_class=school_class,
            )

    return render(
        request,
        "academics/assign_subjects_to_exam.html",
        {
            "form": form,
            "assigned_subjects": assigned_subjects,
            "exam": exam,
            "school_class": school_class,
        },
    )

@login_required
@role_required("schooladmin")
def remove_exam_subject(request, pk):
    exam_subject = get_object_or_404(ExamSubject, pk=pk)

    exam_id = exam_subject.exam.id
    class_id = exam_subject.school_class.id

    if request.method == "POST":
        exam_subject.delete()
        messages.success(request, "Subject removed successfully.")

    return redirect(
        f"/academics/exams/assign-subjects/?exam={exam_id}&class={class_id}"
    )


###trial####

def get_rubric(mark):
    """Return rubric string based on marks."""
    if mark >= 80:
        return "EE"
    elif mark >= 60:
        return "M.E"
    elif mark >= 40:
        return "A.E"
    else:
        return "B.E"


@login_required
@role_required('schooladmin')
def admin_class_marks(request, class_id):
    # Get class and students
    school_class = get_object_or_404(SchoolClass, id=class_id, school=request.user.school)
    students = Student.objects.filter(student_class=school_class)

    # Subjects for this class
    subjects = Subject.objects.filter(
        teachersubjectassignment__school_class=school_class
    ).distinct().order_by('name')

    # Exams that have these subjects
    exams = Exam.objects.filter(
        examsubject__subject__in=subjects
    ).distinct().order_by('year', 'term')

    # Fetch marks
    marks_qs = StudentMark.objects.filter(
        student__in=students,
        subject__in=subjects,
        exam__in=exams
    )
    marks_map = {(m.student_id, m.subject_id, m.exam_id): m.marks for m in marks_qs}

    # Get teacher(s) assigned to this class
    assigned_teachers_qs = TeacherClass.objects.filter(
        school_class=school_class
    ).select_related('teacher', 'teacher__user')
    assigned_teachers = [t.teacher.user.get_full_name() for t in assigned_teachers_qs]

    exam_tables = []

    for exam in exams:
        rows = []
        subject_totals = [{"subject": subj, "total": 0, "count": 0} for subj in subjects]

        for student in students:
            student_total = 0
            student_marks = []
            for i, subject in enumerate(subjects):
                mark = marks_map.get((student.id, subject.id, exam.id), 0)
                student_marks.append({"mark": mark, "rubric": get_rubric(mark)})
                student_total += mark
                subject_totals[i]["total"] += mark
                subject_totals[i]["count"] += 1

            student_avg = student_total / len(subjects) if subjects else 0
            rows.append({
                "student": student,
                "marks": student_marks,
                "total": student_total,
                "average": round(student_avg, 2)
            })

        # Ranking
        rows.sort(key=lambda x: x['total'], reverse=True)
        for idx, row in enumerate(rows):
            row['rank'] = idx + 1

        # Subject means
        for subj_total in subject_totals:
            subj_total["mean"] = round(subj_total["total"] / subj_total["count"], 2) if subj_total["count"] else 0

        max_total = len(subjects) * exam.max_mark if subjects else 0

        exam_tables.append({
            "exam": exam,
            "subjects": subjects,
            "rows": rows,
            "subject_totals": subject_totals,
            "teachers": assigned_teachers, 
            "school": school_class.school,
            "max_total": max_total,
        })

    return render(request, "academics/admin_class_marks.html", {
        "school_class": school_class,
        "exam_tables": exam_tables
    })
@login_required
@role_required('schooladmin')
def admin_class_list(request):
    """
    Admin sees all classes for their school.
    """
    classes = SchoolClass.objects.filter(school=request.user.school)
    return render(request, 'academics/admin_class_list.html', {'classes': classes})
