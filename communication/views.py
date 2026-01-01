from django.shortcuts import render
from communication.models import Notification
from communication.services.notification_service import dispatch_notification


def student_balance(student):
    statement = student_fee_statement(student)
    return statement['balance']

def student_with_fee_balance(school):
    students = Student.objects.filter(school=school)
    return [s for s students if student_balance(s) > 0]

def create_fee_reminder(school):
    return Notification.objects.create(
        school=school,
        title = 'Outstanding Fee Balance',
        message = 'Dear Parent, kindly clear the outstanding school fee balance. Thank you ',
        notification_type = 'fee',
        channel='sms'
    )

def send_fee_reminder(school):
    notification = create_fee_reminder(school)
    students = students_with_fee_balance(school)

    recipients= []

    for student in students:
        parent = student.parent
        recipeints.append({
            'name': parent.full_name,
            'phone': parent.phone_number,
            'email': parent.email,
        })
    disatch_notification(notification, recipeint)

def send_manual_fee_reminders(request, school_id):
    school = School.objects.get(id=schhol_id)
    send_fee_reminder(school)