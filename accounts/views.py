from django.shortcuts import render

from accounts.models import StudentMark, student_attendance

def student_report(Student, exam):
    marks = StudentMark.objects.filter(
        student =  student,
        exam_subject__exam  =  exam
    )
    total = sum(m.marks for m in marks)
    average =  total/ marks.count() if marks.exists() else 0

    return{
        'marks': marks,
        'total': total,
        'average': average,
    }
def student_attendance _summary(student):
    reords = student_attendance.objects.filter(student = student)
    present = records.filter(status='prsent').count()
    absent = records.filter(status='absent').count()
    late = records.filter(satus= 'late').count()

    return{
        'present': present,
        'absent': absent,
        'late': late,
    }
    StudentAttendance.objects.filter(
        student_class=class_obj,
        date__month = 6
    )
