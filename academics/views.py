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
import traceback

from accounts.decorators import role_required
from .models import AcademicTerm, SchoolClass, Subject, Exam, ExamSubject, StudentMark, School
from .forms import SubjectForm, ExamForm, AssignSubjectsToExamForm
from schools.forms import AssignExamForm
from students.models import Student
from teachers.models import Teacher, TeacherClass, TeacherSubjectAssignment
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db import transaction
import json

from students.models import Student
from academics.models import Exam, Subject, StudentMark

User = get_user_model()

from django.http import JsonResponse
@login_required
def load_terms(request):
    year = request.GET.get('year')

    terms = AcademicTerm.objects.filter(
        school=request.user.school,
        year=year
    ).order_by('term')

    options = '<option value="">Select Term</option>'

    for term in terms:
        options += (
            f'<option value="{term.id}">'
            f'{term.term}'
            f'</option>'
        )

    return JsonResponse({
        'options': options
    })


def load_classes(request):
    classes = SchoolClass.objects.all()

    options = '<option value="">Select Class</option>'
    for c in classes:
        options += f'<option value="{c.id}">{c.name} {c.stream}</option>'

    return JsonResponse({'options': options})

def get_selected_term(request):
    school = request.user.school

    year = request.GET.get("year")
    term_name = request.GET.get("term")

    # Explicit selection
    if year and term_name:
        term = AcademicTerm.objects.filter(
            school=school,
            year=year,
            term=term_name
        ).first()

        if term:
            return term

    # Active term
    term = AcademicTerm.objects.filter(
        school=school,
        is_active=True
    ).first()

    if term:
        return term

    # Latest term fallback
    return AcademicTerm.objects.filter(
        school=school
    ).order_by('-year', '-id').first()



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


@login_required
def exam_edit(request, pk):

    exam = get_object_or_404(
        Exam,
        pk=pk,
        school=request.user.school
    )

    if request.method == 'POST':

        form = ExamForm(
            request.POST,
            instance=exam,
            school=request.user.school
        )

        print(form.errors)

        if form.is_valid():

            form.save()

            messages.success(
                request,
                'Exam updated successfully.'
            )

            return redirect('academics:exam_list')

    else:

        form = ExamForm(
            instance=exam,
            school=request.user.school
        )

    return render(
        request,
        'academics/exam_edit.html',
        {
            'form': form,
            'exam': exam
        }
    )


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
    if not term:
        return []

    exams = list(
        Exam.objects.filter(
            school=term.school,
            term=term
        ).select_related('term')
    )

    exam_order = {
        "Opener": 1,
        "Mid-term": 2,
        "End-term": 3,
    }

    exams.sort(
        key=lambda x: exam_order.get(x.exam_type, 99)
    )

    return exams

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

    teacher = None

    # --------------------------------------------------
    # Determine school based on logged-in user's role
    # --------------------------------------------------
    if user.role == "teacher":
        if not hasattr(user, "teacher"):
            messages.error(request, "Teacher profile required.")
            return redirect("academics:class_overview", class_id=class_id)

        teacher = user.teacher
        school = teacher.school

    elif user.role == "schooladmin":
        if not hasattr(user, "school"):
            messages.error(request, "School administrator is not linked to a school.")
            return redirect("academics:exam_list")

        school = user.school

    else:
        raise PermissionDenied

    # --------------------------------------------------
    # Fetch class and exam
    # --------------------------------------------------
    school_class = get_object_or_404(
        SchoolClass,
        id=class_id,
        school=school
    )

    exam = get_object_or_404(
        Exam,
        id=exam_id,
        school=school
    )

    # --------------------------------------------------
    # Ensure the exam is assigned to this class
    # --------------------------------------------------
    exam_subjects = ExamSubject.objects.filter(
        exam=exam,
        school_class=school_class
    )

    if not exam_subjects.exists():
        raise Http404("This exam is not assigned to this class.")

    # --------------------------------------------------
    # Students and subjects
    # --------------------------------------------------
    students = Student.objects.filter(
        student_class=school_class
    ).order_by(
        "user__last_name",
        "user__first_name"
    )

    subjects = Subject.objects.filter(
        examsubject__exam=exam,
        examsubject__school_class=school_class
    ).distinct()

    # --------------------------------------------------
    # Existing marks
    # --------------------------------------------------
    existing_marks = {}

    for mark in StudentMark.objects.filter(
        exam=exam,
        school_class=school_class
    ):
        existing_marks.setdefault(mark.student_id, {})[mark.subject_id] = mark.marks

    # --------------------------------------------------
    # Prepare marks for display
    # --------------------------------------------------
    for student in students:

        student.marks_list = []
        total = 0

        for subject in subjects:

            mark_value = existing_marks.get(student.id, {}).get(subject.id, "")
            grade = ""

            if mark_value != "":
                temp = StudentMark(
                    student=student,
                    subject=subject,
                    exam=exam,
                    marks=mark_value
                )

                grade = temp.grade()
                total += float(mark_value)

            student.marks_list.append({
                "subject": subject,
                "mark": mark_value,
                "grade": grade,
            })

        student.total = total
        student.average = round(
            total / len(subjects), 2
        ) if subjects else 0

    # --------------------------------------------------
    # Save marks
    # --------------------------------------------------
    if request.method == "POST":

        with transaction.atomic():

            for student in students:

                for subject in subjects:

                    value = request.POST.get(
                        f"marks_{student.id}_{subject.id}",
                        ""
                    ).strip()

                    if not value:
                        continue

                    try:
                        mark = float(value)
                        mark = max(0, min(mark, exam.max_mark))
                    except ValueError:
                        mark = 0

                    StudentMark.objects.update_or_create(
                        student=student,
                        subject=subject,
                        exam=exam,
                        defaults={
                            "marks": mark,
                            "school_class": school_class,
                            "facilitator": teacher if teacher else None,
                        },
                    )

        messages.success(request, "Marks saved successfully.")
        return redirect(
            "academics:class_overview",
            class_id=class_id
        )

    # --------------------------------------------------
    # School logo
    # --------------------------------------------------
    school_logo_url = school.logo.url if school.logo else None

    return render(
        request,
        "academics/enter_marks.html",
        {
            "exam": exam,
            "school_class": school_class,
            "students": students,
            "subjects": subjects,
            "school_logo_url": school_logo_url,
        },
    )


@login_required
@role_required("teacher", "schooladmin")
def save_mark_ajax(request):

    if request.method != "POST":
        return JsonResponse(
            {"status": "error", "message": "Invalid request"},
            status=400
        )

    try:
        user = request.user

        # ------------------------------------
        # Determine school
        # ------------------------------------
        if user.role == "teacher":
            if not hasattr(user, "teacher"):
                return JsonResponse(
                    {"status": "error", "message": "Teacher profile not found"},
                    status=403
                )

            school = user.teacher.school

        elif user.role == "schooladmin":
            if not hasattr(user, "school"):
                return JsonResponse(
                    {"status": "error", "message": "School not linked"},
                    status=403
                )

            school = user.school

        else:
            return JsonResponse(
                {"status": "error", "message": "Permission denied"},
                status=403
            )

        # ------------------------------------
        # Read JSON
        # ------------------------------------
        data = json.loads(request.body or "{}")

        student_id = data.get("student_id")
        subject_id = data.get("subject_id")
        exam_id = data.get("exam_id")
        mark = data.get("mark")

        if not all([student_id, subject_id, exam_id]):
            return JsonResponse(
                {"status": "error", "message": "Missing fields"},
                status=400
            )

        # ------------------------------------
        # Convert mark
        # ------------------------------------
        try:
            mark = float(mark) if mark not in [None, "", " "] else 0
        except (TypeError, ValueError):
            return JsonResponse(
                {"status": "error", "message": "Invalid mark"},
                status=400
            )

        # ------------------------------------
        # Fetch objects
        # ------------------------------------
        student = Student.objects.get(
            id=student_id,
            student_class__school=school
        )

        subject = Subject.objects.get(
            id=subject_id,
            school=school
        )

        exam = Exam.objects.get(
            id=exam_id,
            school=school
        )

        # Limit mark to exam maximum
        mark = max(0, min(mark, exam.max_mark))

        # ------------------------------------
        # Save mark
        # ------------------------------------
        obj, created = StudentMark.objects.update_or_create(
            student=student,
            subject=subject,
            exam=exam,
            defaults={
                "marks": int(mark),
                "school_class": student.student_class,
                "facilitator": user,   # teacher OR schooladmin
            }
        )

        return JsonResponse({
            "status": "ok",
            "created": created,
            "mark": obj.marks,
        })

    except Student.DoesNotExist:
        return JsonResponse(
            {"status": "error", "message": "Student not found"},
            status=404
        )

    except Subject.DoesNotExist:
        return JsonResponse(
            {"status": "error", "message": "Subject not found"},
            status=404
        )

    except Exam.DoesNotExist:
        return JsonResponse(
            {"status": "error", "message": "Exam not found"},
            status=404
        )

    except Exception:
        print(traceback.format_exc())
        return JsonResponse(
            {"status": "error", "message": "Internal server error"},
            status=500
        )


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
        return "No assessment data."

    avg = sum(marks_list) / len(marks_list)
    trend = trends[-1]["trend"] if trends else "same"

    # Base remark
    if avg >= 80:
        remark = "Excellent performance."
    elif avg >= 65:
        remark = "Good performance."
    elif avg >= 50:
        remark = "Fair performance."
    else:
        remark = "Needs improvement."

    # Trend
    if trend == "up":
        remark += " Improving."
    elif trend == "down":
        remark += " Declining."
    else:
        remark += " Consistent."

    # Subject-specific advice
    subject = subject.lower()

    subject_feedback = {
        "mathematics": {
            "high": "Strong problem-solving.",
            "low": "Practise calculations."
        },
        "english": {
            "high": "Good communication skills.",
            "low": "Improve reading and writing."
        },
        "science": {
            "high": "Good scientific understanding.",
            "low": "Strengthen scientific concepts."
        },
        "kiswahili": {
            "high": "Good language skills.",
            "low": "Improve grammar and vocabulary."
        },
        "social studies": {
            "high": "Good understanding of concepts.",
            "low": "Revise key concepts."
        },
        "creative arts": {
            "high": "Shows creativity.",
            "low": "Participate more actively."
        },
        "agriculture": {
            "high": "Good practical understanding.",
            "low": "Improve practical application."
        },
        "pre-technical studies": {
            "high": "Good technical skills.",
            "low": "Practise practical skills."
        }
    }

    feedback = subject_feedback.get(subject)

    if feedback:
        remark += " " + (feedback["high"] if avg >= 50 else feedback["low"])

    return remark


def generate_overall_remark(avg):
    if avg >= 80:
        return "Excellent performance. Keep it up."
    elif avg >= 65:
        return "Good performance. Aim higher."
    elif avg >= 50:
        return "Fair performance. More effort needed."
    else:
        return "Needs significant improvement."

# ===============================
# 🔹 MAIN VIEW
# ===============================
@login_required
@role_required('schooladmin', 'teacher')
def class_report(request, class_id=None):
    school = request.user.school

    # ============================================================
    # DROPDOWN DATA
    # ============================================================
    classes = (
        SchoolClass.objects
        .filter(school=school)
        .order_by('name', 'stream')
    )

    years = (
        AcademicTerm.objects
        .filter(school=school)
        .values_list('year', flat=True)
        .distinct()
        .order_by('-year')
    )

    selected_class_id = class_id or request.GET.get('class')
    selected_year = request.GET.get('year')
    selected_term_id = request.GET.get('term')

    # ============================================================
    # VALIDATE CLASS
    # ============================================================
    if not selected_class_id:
        messages.error(request, "Please select a class to view reports.")
        return redirect('academics:report_list')

    school_class = get_object_or_404(
        SchoolClass,
        id=selected_class_id,
        school=school
    )

    # ============================================================
    # GET TERMS
    # ============================================================
    terms = AcademicTerm.objects.filter(
        school=school
    ).order_by('-year', 'term')

    # ============================================================
    # DETERMINE SELECTED TERM
    # ============================================================
    selected_term = None

    if selected_term_id:
        selected_term = get_object_or_404(
            AcademicTerm,
            id=selected_term_id,
            school=school
        )

        # IMPORTANT:
        # If both year and term were supplied, make sure the
        # selected term actually belongs to that year.
        if selected_year and str(selected_term.year) != str(selected_year):
            messages.error(
                request,
                "The selected term does not belong to the selected year."
            )
            return redirect(
                f"{request.path}?class={selected_class_id}"
            )

    elif selected_year:
        # If only year was selected, do NOT mix terms.
        selected_term = (
            AcademicTerm.objects
            .filter(
                school=school,
                year=selected_year
            )
            .order_by('term')
            .first()
        )

    else:
        # No filter supplied: use active term.
        selected_term = (
            AcademicTerm.objects
            .filter(
                school=school,
                is_active=True
            )
            .first()
        )

    # ============================================================
    # NO TERM FOUND
    # ============================================================
    if not selected_term:
        messages.warning(
            request,
            "Please select a valid academic year and term."
        )

        return render(
            request,
            "academics/class_report.html",
            {
                "classes": classes,
                "selected_class_id": int(selected_class_id),
                "selected_year": selected_year,
                "selected_term": None,
                "school_class": school_class,
                "exams": [],
                "filtered_reports": [],
                "years": years,
                "terms": terms,
                "school": school,
                "now": timezone.now(),
            }
        )

    # ============================================================
    # IMPORTANT:
    # GET ONLY EXAMS BELONGING TO THIS EXACT TERM
    # ============================================================
    exams_qs = (
        Exam.objects
        .filter(
            school=school,
            term=selected_term,
            examsubject__school_class=school_class
        )
        .distinct()
    )

    # ============================================================
    # EXAM ORDER
    # ============================================================
    EXAM_ORDER = {
        'Opener': 1,
        'Mid-term': 2,
        'End-term': 3,
    }

    exams = list(exams_qs)

    exams.sort(
        key=lambda exam: EXAM_ORDER.get(
            exam.exam_type,
            99
        )
    )

    # ============================================================
    # FETCH ONLY MARKS FOR THESE EXAMS
    # ============================================================
    students = Student.objects.filter(
        student_class=school_class
    ).select_related('user')

    subjects = (
        Subject.objects
        .filter(
            examsubject__school_class=school_class,
            examsubject__exam__term=selected_term
        )
        .distinct()
        .order_by('name')
    )

    all_marks = StudentMark.objects.filter(
        student__in=students,
        subject__in=subjects,
        exam__in=exams,
        exam__term=selected_term,
        school_class=school_class
    )

    # ============================================================
    # FAST MARK LOOKUP
    # ============================================================
    marks_map = {
        (m.student_id, m.subject_id, m.exam_id): m.marks
        for m in all_marks
    }

    # ============================================================
    # BUILD REPORTS
    # ============================================================
    filtered_reports = []

    for student in students:

        report_rows = []

        exam_totals = [0] * len(exams)
        exam_counts = [0] * len(exams)

        for subject in subjects:

            marks_list = []

            # --------------------------------------------
            # Get marks ONLY from exams in selected term
            # --------------------------------------------
            for idx, exam in enumerate(exams):

                mark = marks_map.get(
                    (
                        student.id,
                        subject.id,
                        exam.id
                    ),
                    0
                )

                marks_list.append(mark)

                if mark > 0:
                    exam_totals[idx] += mark
                    exam_counts[idx] += 1

            # --------------------------------------------
            # Trends
            # --------------------------------------------
            trends = []

            for i, mark in enumerate(marks_list):

                if i == 0:
                    trend = 'same'

                else:
                    previous = marks_list[i - 1]

                    if mark > previous:
                        trend = 'up'

                    elif mark < previous:
                        trend = 'down'

                    else:
                        trend = 'same'

                trends.append({
                    'mark': mark,
                    'trend': trend
                })

            # --------------------------------------------
            # Dynamic remark
            # --------------------------------------------
            remark = generate_dynamic_remark(
                subject.name,
                marks_list,
                trends
            )

            report_rows.append({
                'subject': subject.name,
                'marks': trends,
                'remarks': remark,
            })

        # ====================================================
        # EXAM AVERAGES
        # ====================================================
        exam_averages = [
            round(
                exam_totals[i] / exam_counts[i],
                1
            )
            if exam_counts[i]
            else 0

            for i in range(len(exams))
        ]

        # ====================================================
        # OVERALL AVERAGE
        # ====================================================
        overall_avg = (
            round(
                sum(exam_averages) / len(exam_averages),
                1
            )
            if exam_averages
            else 0
        )

        overall_remark = generate_overall_remark(
            overall_avg
        )

        # ====================================================
        # FACILITATOR
        # ====================================================
        student_marks = all_marks.filter(
            student=student
        )

        facilitator = (
            student_marks.first().facilitator
            if student_marks.exists()
            else None
        )

        filtered_reports.append({
            'student': student,
            'report_rows_with_trends': report_rows,
            'exam_totals': exam_totals,
            'exam_averages': exam_averages,
            'overall_avg': overall_avg,
            'overall_remark': overall_remark,

            # IMPORTANT:
            # Always use the actual selected term
            'exam_year': selected_term.year,
            'exam_term': selected_term.term,

            'facilitator': facilitator,
        })

    # ============================================================
    # RENDER
    # ============================================================
    return render(
        request,
        'academics/class_report.html',
        {
            'classes': classes,
            'selected_class_id': int(selected_class_id),
            'selected_year': selected_term.year,
            'selected_term': selected_term,
            'school_class': school_class,
            'exams': exams,
            'filtered_reports': filtered_reports,
            'years': years,
            'terms': terms,
            'school': school,
            'now': timezone.now(),
        }
    )

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

    classes = SchoolClass.objects.filter(school=school).order_by("name", "stream")

    if request.method == "POST":
        form = AssignSubjectsToExamForm(request.POST, school=school)

        if form.is_valid():
            exam = form.cleaned_data["exam"]
            school_classes = form.cleaned_data["school_class"]
            subjects = form.cleaned_data["subjects"]

            for cls in school_classes:
                for subject in subjects:
                    ExamSubject.objects.get_or_create(
                        exam=exam,
                        school_class=cls,
                        subject=subject,
                    )

            first_class = school_classes.first()
            messages.success(request, "Subjects assigned successfully.")

            return redirect(
                f"{request.path}?exam={exam.id}&class={first_class.id if first_class else ''}"
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

    return render(request, "academics/assign_subjects_to_exam.html", {
        "form": form,
        "classes": classes,
        "assigned_subjects": assigned_subjects,
        "exam": exam,
        "school_class": school_class,
        "selected_class_ids": [],
        "assigned_ids": [],
    })

@login_required
@role_required("schooladmin")
def remove_exam_subject(request, pk):
    exam_subject = get_object_or_404(
        ExamSubject,
        pk=pk,
        exam__school=request.user.school
    )

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

    # =========================
    # STUDENTS
    # =========================
    students = (
        Student.objects.filter(student_class=school_class)
        .select_related('user')
        .order_by('user__first_name', 'user__last_name')
    )

    # =========================
    # SUBJECTS
    # =========================
    subjects = list(
        Subject.objects.filter(
            teachersubjectassignment__school_class=school_class
        )
        .distinct()
        .order_by('name')
    )

    subject_count = len(subjects)

    # =========================
    # TERM FILTERS
    # =========================
    years = (
        AcademicTerm.objects.filter(school=school)
        .values_list('year', flat=True)
        .distinct()
        .order_by('-year')
    )

    terms = (
        AcademicTerm.objects.filter(school=school)
        .order_by('-year', 'term')
    )

    selected_year = request.GET.get('year')
    selected_term = request.GET.get('term')

    term = None

    if selected_year and selected_term:
        term = AcademicTerm.objects.filter(
            school=school,
            year=selected_year,
            term=selected_term
        ).first()

    if not term:
        term = AcademicTerm.objects.filter(
            school=school,
            is_active=True
        ).first()

    if not term:
        messages.error(request, "No academic term has been configured.")
        return render(request, "academics/admin_class_marks.html", {
            "school_class": school_class,
            "term": None,
            "exam_tables": [],
            "years": years,
            "terms": terms,
            "selected_year": selected_year,
            "selected_term": selected_term,
        })

    # =========================
    # EXAMS
    # =========================
    exam_order = {
        "Opener": 1,
        "Mid-term": 2,
        "End-term": 3,
    }

    exams = list(
        Exam.objects.filter(
            school=school,
            term=term
        )
    )

    exams.sort(key=lambda x: exam_order.get(x.exam_type, 99))

    if not exams:
        messages.warning(
            request,
            f"No exams found for {term.term} {term.year}."
        )

    # =========================
    # MARKS MAP (FAST LOOKUP)
    # =========================
    marks_qs = StudentMark.objects.filter(
        student__in=students,
        subject__in=subjects,
        exam__in=exams
    )

    marks_map = {
        (m.student_id, m.subject_id, m.exam_id): m.marks
        for m in marks_qs
    }

    # =========================
    # TEACHERS (FIXED)
    # =========================
    teacher_qs = (
        TeacherSubjectAssignment.objects
        .filter(school_class=school_class)
        .select_related('teacher__user')
    )

    teachers = list({
        t.teacher.id: t.teacher
        for t in teacher_qs
    }.values())

    # =========================
    # BUILD EXAM TABLES
    # =========================
    exam_tables = []

    for exam in exams:

        rows = []

        subject_totals = [
            {"subject": subject, "total": 0, "count": 0}
            for subject in subjects
        ]

        for student in students:

            student_total = 0
            student_marks = []

            for i, subject in enumerate(subjects):

                mark = marks_map.get(
                    (student.id, subject.id, exam.id)
                )

                student_marks.append({
                    "mark": mark if mark is not None else "-",
                    "numeric_mark": mark or 0,
                    "rubric": get_rubric(mark) if mark is not None else ""
                })

                if mark is not None:
                    student_total += mark
                    subject_totals[i]["total"] += mark
                    subject_totals[i]["count"] += 1

            average = round(student_total / subject_count, 2) if subject_count else 0

            rows.append({
                "student": student,
                "marks": student_marks,
                "total": student_total,
                "average": average
            })

        # =========================
        # RANKING
        # =========================
        rows.sort(key=lambda x: x["total"], reverse=True)

        rank = 1
        prev = None

        for idx, row in enumerate(rows):
            if prev is not None and row["total"] < prev:
                rank = idx + 1

            row["rank"] = rank
            prev = row["total"]

        # =========================
        # SUBJECT MEANS
        # =========================
        for item in subject_totals:
            item["mean"] = (
                round(item["total"] / item["count"], 2)
                if item["count"] else 0
            )

        # =========================
        # CLASS MEAN
        # =========================
        class_mean = (
            round(sum(r["average"] for r in rows) / len(rows), 2)
            if rows else 0
        )

        # =========================
        # BUILD TABLE
        # =========================
        exam_tables.append({
            "exam": exam,
            "subjects": subjects,
            "rows": rows,
            "subject_totals": subject_totals,
            "teachers": teachers,
            "school": school,
            "max_total": subject_count * exam.max_mark,
            "class_mean": class_mean,
            "student_count": len(rows),
        })

    # =========================
    # RENDER
    # =========================
    return render(request, "academics/admin_class_marks.html", {
        "school_class": school_class,
        "term": term,
        "exam_tables": exam_tables,
        "years": years,
        "terms": terms,
        "selected_year": selected_year,
        "selected_term": selected_term,
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

@login_required
@role_required("schooladmin")
def unassign_exam_class(request, exam_id, class_id):
    exam = get_object_or_404(
        Exam,
        id=exam_id,
        school=request.user.school
    )

    school_class = get_object_or_404(
        SchoolClass,
        id=class_id,
        school=request.user.school
    )

    if request.method == "POST":

        # Prevent removing an exam if marks already exist
        if StudentMark.objects.filter(
            exam=exam,
            school_class=school_class
        ).exists():

            messages.error(
                request,
                "Marks have already been entered for this class. Delete the marks first."
            )
            return redirect("academics:exam_list")

        ExamSubject.objects.filter(
            exam=exam,
            school_class=school_class
        ).delete()

        messages.success(
            request,
            f"{school_class.name} has been removed from the exam."
        )

    return redirect("academics:exam_list")