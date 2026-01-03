from students.models import Student
from teachers.models import Teacher

def can_add_student(school):
    plan = school.subscription
    if not plan:
        return False
    return Student.objects.filter(school=school).count() < plan.max_students


def can_add_teacher(school):
    plan = school.subscription
    if not plan:
        return False
    return Teacher.objects.filter(school=school).count() < plan.max_teachers