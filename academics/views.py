from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.http import Http404, JsonResponse
from django.db import transaction
from django.utils import timezone
import json
from django.http import JsonResponse
from .models import AcademicTerm
from schools.models import School

from accounts.decorators import role_required
from .models import AcademicTerm, SchoolClass, Subject, Exam, ExamSubject, StudentMark, School
from .forms import SubjectForm, ExamForm, AssignSubjectsToExamForm
from schools.forms import AssignExamForm
from students.models import Student
from teachers.models import Teacher, TeacherClass, TeacherSubjectAssignment
from django.contrib.auth import get_user_model

User = get_user_model()

from django.http import JsonResponse

def load_terms(request):
    year = request.GET.get('year')
    terms = Term.objects.filter(year=year)
    options = '<option value="">Select Term</option>'
    for term in terms:
        options += f'<option value="{term.id}">{term.name}</option>'

    return JsonResponse({'options': options})


def load_classes(request):
    classes = SchoolClass.objects.all()

    options = '<option value="">Select Class</option>'
    for c in classes:
        options += f'<option value="{c.id}">{c.name} {c.stream}</option>'

    return JsonResponse({'options': options})


def get_selected_term(request):
    school = request.user.school

    year = request.GET.get('year')
    term_name = request.GET.get('term')

    if year and term_name:
        return AcademicTerm.objects.filter(
            school=school,
            year=year,
            term=term_name
        ).first()

    # fallback → ACTIVE TERM
    return AcademicTerm.objects.filter(
        school=school,
        is_active=True
    ).first()



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
    school = request.user.school

    exams = (
        Exam.objects
        .filter(school=school)
        .order_by('-term__year', '-term__term', 'exam_type')
    )

    for exam in exams:
        exam.assigned_classes = (
            SchoolClass.objects.filter(
                examsubject__exam=exam
            ).distinct()
        )

    if request.method == 'POST':
        exam_id = request.POST.get('exam_id')
        exam = get_object_or_404(Exam, id=exam_id, school=school)

        form = AssignExamForm(request.POST, user=request.user)
        if form.is_valid():
            classes = form.cleaned_data['classes']
            for school_class in classes:
                for subject in Subject.objects.filter(school=school):
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
    school = request.user.school  

    if request.method == 'POST':
        form = ExamForm(request.POST, school=school)
        if form.is_valid():
            exam_type = form.cleaned_data['exam_type']
            term = form.cleaned_data['term']

            
            existing_exam = Exam.objects.filter(
                school=school,
                term=term,
                exam_type=exam_type
            ).first()

            if existing_exam:
                messages.error(request, f"{exam_type.capitalize()} exam already exists for {term}.")
            else:
                exam = form.save(commit=False)
                exam.school = school  
                exam.save()
                messages.success(request, "Exam saved successfully!")
                return redirect('academics:exam_list')  
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ExamForm(school=school)

    context = {
        'form': form
    }
    return render(request, 'academics/exam_add.html', context)

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
    exam = get_object_or_404(Exam, pk=pk, school=request.user.school)
    
    if request.method == 'POST':
        form = ExamForm(request.POST, instance=exam, school=request.user.school)
        if form.is_valid():
            form.save()
            messages.success(request, 'Exam updated successfully.')
            return redirect('academics:exam_list')
    else:
        form = ExamForm(instance=exam)
    
    return render(request, 'academics/exam_edit.html', {'form': form, 'exam': exam})


def exam_delete(request, pk):
    exam = get_object_or_404(Exam, pk=pk, school=request.user.school)
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


def get_term_exams(term):
 
    exam_order = ['Opener', 'Mid-term', 'End-term']
    exams = Exam.objects.filter(term=term, school=term.school)
    ordered_exams = []

    for ex_type in exam_order:
        ex = exams.filter(exam_type=ex_type).first() 
        if ex:
            ordered_exams.append(ex)
    
    return ordered_exams

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
    ).select_related('exam').order_by('-exam__term__year', '-exam__term__term', 'exam__exam_type')

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
@role_required('teacher', 'schooladmin')
def enter_marks(request, class_id, exam_id):
    user = request.user

   
    if not hasattr(user, 'teacher'):
        messages.error(request, "Teacher profile required to enter marks.")
        return redirect('academics:class_overview', class_id=class_id)
    teacher = user.teacher
    school = teacher.school

    school_class = get_object_or_404(SchoolClass,id=class_id,school=school)

    exam = get_object_or_404(Exam,id=exam_id,school=school)

    exam_subjects = ExamSubject.objects.filter(exam=exam,school_class=school_class)

    if not exam_subjects.exists():
        raise Http404("This exam is not assigned to this class")

    students = Student.objects.filter(student_class=school_class).order_by('user__last_name', 'user__first_name')

    subjects = Subject.objects.filter(examsubject__exam=exam,examsubject__school_class=school_class).distinct()

    existing_marks = {}
    for m in StudentMark.objects.filter(exam=exam,school_class=school_class):
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
                                #'term': exam.term,
                                'facilitator': teacher  
                            }
                        )

        messages.success(request, "Marks saved successfully.")
        return redirect('academics:class_overview', class_id=class_id)

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
    school = request.user.teacher.school

    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "Invalid request"}, status=400)

    try:
        data = json.loads(request.body)

        student_id = data.get("student_id")
        subject_id = data.get("subject_id")
        exam_id = data.get("exam_id")
        marks = data.get("mark")

        marks = float(marks)

        student = Student.objects.get(id=student_id, student_class__school=school)
        exam = Exam.objects.get(id=exam_id, school=school)
        subject = Subject.objects.get(id=subject_id, school=school)

        StudentMark.objects.update_or_create(
            student=student,
            subject=subject,
            exam=exam,
            defaults={
                "marks": marks,
                "school_class": student.student_class,
                #"term": exam.term,
                "facilitator": request.user
            }
        )

        return JsonResponse({"status": "ok"})

    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)

@login_required
def student_report(request, student_id):
    school = request.user.school
    student = get_object_or_404(Student, id=student_id, student_class__school=school)
    subjects = Subject.objects.filter(
        teachersubjectassignment__school_class=student.student_class
    ).distinct().order_by('name')

    term_param = request.GET.get('term')
    year_param = request.GET.get('year')

    try:
        term_id = int(term_param) if term_param and term_param != 'None' else None
    except ValueError:
        term_id = None

    try:
        year = int(year_param) if year_param and year_param != 'None' else None
    except ValueError:
        year = None

    term_qs = AcademicTerm.objects.filter(school=school).order_by('-year', '-term')
    if term_id:
        term_qs = term_qs.filter(id=term_id)
    elif year:
        term_qs = term_qs.filter(year=year)
   
    term = term_qs.first()
    if not term:
        term = AcademicTerm.objects.filter(school=school).order_by('-year', '-term').first()
    if not term:
        messages.error(request, "No active term found for this class.")
        return redirect('academics:report_list')

    exams = Exam.objects.filter(
        id__in=ExamSubject.objects.filter(
            school_class=student.student_class,
            exam__term=term
        ).values_list('exam_id', flat=True)
    ).order_by('exam_type')

    no_exams = not exams.exists()  # <-- Flag for template

    marks_qs = StudentMark.objects.filter(student=student, subject__in=subjects, exam__in=exams)
    marks_map = {(m.exam_id, m.subject_id): m for m in marks_qs}

    report_rows = []
    exam_totals = [0] * len(exams)
    exam_counts = [0] * len(exams)

    for subject in subjects:
        marks_list = []
        trends = []
        total_marks = 0
        count_marks = 0

        for idx, exam in enumerate(exams):
            mark_obj = marks_map.get((exam.id, subject.id))
            mark = mark_obj.marks if mark_obj else 0
            marks_list.append(mark)
            exam_totals[idx] += mark
            if mark > 0:
                exam_counts[idx] += 1

            total_marks += mark
            if mark > 0:
                count_marks += 1

        for i, mark in enumerate(marks_list):
            if i == 0:
                trend = 'same'
            else:
                prev = marks_list[i - 1]
                trend = 'up' if mark > prev else 'down' if mark < prev else 'same'
            trends.append({'mark': mark, 'trend': trend})

        avg = total_marks / count_marks if count_marks else 0
        if avg >= 80:
            remark = 'Exceeding Expectation'
        elif avg >= 60:
            remark = 'Meeting Expectation'
        elif avg >= 40:
            remark = 'Approaching Expectation'
        else:
            remark = 'Below Expectation'

        report_rows.append({
            'subject': subject.name,
            'marks': trends,
            'remarks': remark
        })

    exam_averages = [
        round(exam_totals[i] / exam_counts[i], 2) if exam_counts[i] else 0
        for i in range(len(exams))
    ]

    return render(request, 'academics/student_report.html', {
        'student': student,
        'term': term,
        'exams': exams,
        'report_rows_with_trends': report_rows,
        'exam_averages': exam_averages,
        'school': school,
        'no_exams': no_exams,  # <-- Pass flag
    })



@login_required
@role_required('schooladmin')
def report_list(request):
    school = request.user.school
    classes = SchoolClass.objects.filter(school=school)

    # Available years from AcademicTerm (better than Exam)
    years = AcademicTerm.objects.filter(school=school).values_list('year', flat=True).distinct().order_by('-year')
    terms = AcademicTerm.objects.filter(school=school).order_by('-year', 'term')

    # Get selected year & term from GET params
    selected_year = request.GET.get('year')
    selected_term_id = request.GET.get('term')

    selected_term = None
    if selected_year and selected_term_id:
        selected_term = AcademicTerm.objects.filter(
            id=selected_term_id,
            year=selected_year,
            school=school
        ).first()

    return render(request, 'academics/report_list.html', {
        'classes': classes,
        'years': years,
        'terms': terms,
        'selected_year': selected_year,
        'selected_term': selected_term,
    })



# ===============================
# 🔹 DYNAMIC REMARK GENERATORS
# ===============================

def generate_dynamic_remark(subject, marks_list, trends):
    if not marks_list:
        return "No assessment data available."

    avg = sum(marks_list) / len(marks_list)
    latest = marks_list[-1]
    trend = trends[-1]["trend"] if trends else "same"

    # --- Base performance ---
    if avg >= 80:
        remark = "Excellent performance"
    elif avg >= 65:
        remark = ""
    elif avg >= 50:
        remark = "More effort required."
    else:
        remark = "Significant improvement needed."

    # --- Trend insight ---
    if trend == "up":
        remark += " Showing improvement."
    elif trend == "down":
        remark += " Performance is declining."
    else:
        remark += " Performance is consistent."

    subject_lower = subject.lower()

    # --- Subject‑specific feedback ---
    if subject_lower == "mathematics":
        if avg < 50:
            remark += " Needs more practice in calculations and problem‑solving."
        else:
            remark += " Demonstrates strong numerical understanding."

    elif subject_lower == "english":
        if avg < 50:
            remark += " Should improve reading and writing skills."
        else:
            remark += " Shows good language and comprehension skills."

    elif subject_lower == "science":
        remark += " Continue developing scientific concepts "

    else:
        # Default for subjects not explicitly configured
        if avg < 50:
            remark += " Needs more effort and support."
        else:
            remark += " "

    return remark

def generate_overall_remark(avg):
    if avg >= 80:
        return " Keep up the excellent work."
    elif avg >= 65:
        return "There is room for further improvement."
    elif avg >= 50:
        return "More effort and consistency are needed."
    else:
        return "Immediate improvement and support required."


# ===============================
# 🔹 MAIN VIEW
# ===============================

@login_required
@role_required('schooladmin', 'teacher')
def class_report(request, class_id=None):
    school = request.user.school

    # --- Dropdown data ---
    classes = SchoolClass.objects.filter(school=school).order_by('name')
    years = AcademicTerm.objects.filter(school=school).values_list('year', flat=True).distinct()
    terms = AcademicTerm.objects.filter(school=school).order_by('-year', 'term')

    # --- Selected filters ---
    selected_class_id = class_id or request.GET.get('class')
    selected_year = request.GET.get('year')
    selected_term_id = request.GET.get('term')

    if not selected_class_id:
        messages.error(request, "Please select a class to view reports.")
        return redirect('academics:report_list')

    school_class = get_object_or_404(SchoolClass, id=selected_class_id, school=school)

    students = Student.objects.filter(student_class=school_class)
    subjects = Subject.objects.filter(
        examsubject__school_class=school_class
    ).distinct().order_by('name')

    # --- Exams ---
    exams_qs = Exam.objects.filter(
        id__in=ExamSubject.objects.filter(
            school_class=school_class
        ).values_list('exam_id', flat=True)
    )

    # --- Filter by term/year ---
    selected_term = None
    if selected_term_id:
        selected_term = get_object_or_404(AcademicTerm, id=selected_term_id, school=school)
        exams_qs = exams_qs.filter(term=selected_term)

    if selected_year:
        exams_qs = exams_qs.filter(term__year=selected_year)

    # --- Custom exam ordering ---
    EXAM_ORDER = ['Opener', 'Mid-term', 'End-term']
    exam_order_dict = {name: idx for idx, name in enumerate(EXAM_ORDER)}

    exams = list(exams_qs)
    exams.sort(key=lambda x: (x.term.year, x.term.term, exam_order_dict.get(x.exam_type, 99)))

    # --- Fetch marks ---
    all_marks = StudentMark.objects.filter(
        student__in=students,
        subject__in=subjects,
        exam__in=exams
    )

    marks_map = {
        (m.student_id, m.subject_id, m.exam_id): m.marks
        for m in all_marks
    }

    # ===============================
    # 🔹 BUILD REPORTS
    # ===============================
    filtered_reports = []

    for student in students:
        report_rows = []
        exam_totals = [0] * len(exams)
        exam_counts = [0] * len(exams)

        for subject in subjects:
            marks_list = []

            # --- Collect marks ---
            for idx, exam in enumerate(exams):
                mark = marks_map.get((student.id, subject.id, exam.id), 0)
                marks_list.append(mark)

                if mark > 0:
                    exam_totals[idx] += mark
                    exam_counts[idx] += 1

            # --- Compute trends ---
            trends = []
            for i, mark in enumerate(marks_list):
                if i == 0:
                    trend = 'same'
                else:
                    prev = marks_list[i - 1]
                    if mark > prev:
                        trend = 'up'
                    elif mark < prev:
                        trend = 'down'
                    else:
                        trend = 'same'

                trends.append({'mark': mark, 'trend': trend})

            # --- Dynamic remark ---
            remark = generate_dynamic_remark(subject.name, marks_list, trends)

            report_rows.append({
                'subject': subject.name,
                'marks': trends,
                'remarks': remark,
            })

        # --- Exam averages ---
        exam_averages = [
            round(exam_totals[i] / exam_counts[i], 1) if exam_counts[i] else 0
            for i in range(len(exams))
        ]

        # --- Overall average ---
        overall_avg = round(sum(exam_averages) / len(exam_averages), 1) if exam_averages else 0

        # --- Overall remark ---
        overall_remark = generate_overall_remark(overall_avg)

        filtered_reports.append({
            'student': student,
            'report_rows_with_trends': report_rows,
            'exam_totals': exam_totals,
            'exam_averages': exam_averages,
            'overall_avg': overall_avg,
            'overall_remark': overall_remark,
            'exam_year': selected_year,
            'exam_term': selected_term.term if selected_term else None,
            'facilitator': getattr(student.student_class, 'facilitator', None),
        })

    return render(request, 'academics/class_report.html', {
        'classes': classes,
        'selected_class_id': int(selected_class_id),
        'selected_year': selected_year,
        'selected_term': selected_term,
        'school_class': school_class,
        'exams': exams,
        'filtered_reports': filtered_reports,
        'years': years,
        'terms': terms,
        'school': school,
        'now': timezone.now(),
    })

@login_required
@role_required('schooladmin')
def assign_teacher(request):
    school = request.user.school
    if request.method == "POST":
        teacher = get_object_or_404(Teacher, id=request.POST['teacher'], school=school)
        school_class = get_object_or_404(SchoolClass, id=request.POST['school_class'], school=school)
        subject = get_object_or_404(Subject, id=request.POST['subject'], school=school)

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
        'teachers': Teacher.objects.filter(school=request.user.school),
        'classes': SchoolClass.objects.filter(school=request.user.school),
        'subjects': Subject.objects.filter(school=request.user.school),
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
    school = request.user.school
    assigned_subjects = ExamSubject.objects.none()
    exam = None
    school_class = None

    if request.method == "POST":
        form = AssignSubjectsToExamForm(request.POST,school=school)

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
        form = AssignSubjectsToExamForm(school=school)
        exam_id = request.GET.get("exam")
        class_id = request.GET.get("class")

        if exam_id and class_id:
            exam = get_object_or_404(Exam, id=exam_id, school=school)
            school_class = get_object_or_404(SchoolClass, id=class_id, school=school)

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
    exam_subject = get_object_or_404(ExamSubject, pk=pk,exam__school=request.user.school)

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
    school = request.user.school

    school_class = get_object_or_404(
        SchoolClass,
        id=class_id,
        school=school
    )

    students = Student.objects.filter(student_class=school_class)

    subjects = Subject.objects.filter(
        teachersubjectassignment__school_class=school_class
    ).distinct().order_by('name')

    # ✅ Term selection
    term = get_selected_term(request)
    if not term:
        messages.error(request, "No term selected.")
        return redirect('academics:admin_class_list')

    # ✅ Exams (Opener → Mid → End)
    exams = get_term_exams(term)

    # ✅ Marks
    marks_qs = StudentMark.objects.filter(
        student__in=students,
        subject__in=subjects,
        exam__in=exams
    )

    marks_map = {
        (m.student_id, m.subject_id, m.exam_id): m.marks
        for m in marks_qs
    }

    # ✅ Teachers
    assigned_teachers = [
        t.teacher.user.get_full_name()
        for t in TeacherClass.objects.filter(
            school_class=school_class
        ).select_related('teacher__user')
    ]

    exam_tables = []

    for exam in exams:
        rows = []
        subject_totals = [
            {"subject": subj, "total": 0, "count": 0}
            for subj in subjects
        ]

        for student in students:
            student_total = 0
            student_marks = []

            for i, subject in enumerate(subjects):
                mark = marks_map.get((student.id, subject.id, exam.id), 0)

                student_marks.append({
                    "mark": mark,
                    "rubric": get_rubric(mark)
                })

                student_total += mark

                # ✅ FIXED counting
                subject_totals[i]["total"] += mark
                if mark > 0:
                    subject_totals[i]["count"] += 1

            student_avg = student_total / len(subjects) if subjects else 0

            rows.append({
                "student": student,
                "marks": student_marks,
                "total": student_total,
                "average": round(student_avg, 2)
            })

        # ✅ Ranking
        rows.sort(key=lambda x: x['total'], reverse=True)
        for idx, row in enumerate(rows):
            row['rank'] = idx + 1

        # ✅ Subject means
        for subj_total in subject_totals:
            subj_total["mean"] = (
                round(subj_total["total"] / subj_total["count"], 2)
                if subj_total["count"] else 0
            )

        max_total = len(subjects) * exam.max_mark if subjects else 0

        exam_tables.append({
            "exam": exam,
            "subjects": subjects,
            "rows": rows,
            "subject_totals": subject_totals,
            "teachers": assigned_teachers,
            "school": school,
            "max_total": max_total,
        })

    return render(request, "academics/admin_class_marks.html", {
        "school_class": school_class,
        "term": term,
        "exam_tables": exam_tables
    })


@login_required
@role_required('schooladmin')
def admin_class_list(request):
   
    classes = SchoolClass.objects.filter(school=request.user.school)
    return render(request, 'academics/admin_class_list.html', {'classes': classes})

def student_results(request, student_id):
    student = get_object_or_404(
        Student,
        id=student_id,
        student_class__school=request.user.school
    )

    marks = StudentMark.objects.filter(student=student).select_related('subject', 'exam')

    results_by_exam = {}
    for mark in marks:
        exam_name = f"{mark.exam.exam_type} ({mark.exam.term.term} {mark.exam.term.year})"
        results_by_exam.setdefault(exam_name, []).append(mark)

    return render(request, 'academics/student_results.html', {
        'student': student,
        'results_by_exam': results_by_exam
    })