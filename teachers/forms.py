from django import forms
from .models import Teacher
from .models import TeacherSubjectAssignment
from academics.models import Subject
from academics.models import Subject, SchoolClass



class TeacherProfileForm(forms.ModelForm):
    class Meta:
        model = Teacher
        fields = [
            'phone',
            'date_of_birth',
            'gender',
            'designation',
            'qualification',
            'specialization',
            'profile_picture',
        ]


class TeacherSubjectAssignmentForm(forms.ModelForm):
    class Meta:
        model = TeacherSubjectAssignment
        fields = ['teacher', 'subject', 'school_class']

    def __init__(self, *args, **kwargs):
        school = kwargs.pop('school', None)
        super().__init__(*args, **kwargs)

        if school:
            self.fields['teacher'].queryset = Teacher.objects.filter(school=school)
            self.fields['subject'].queryset = Subject.objects.filter(school=school)
            self.fields['school_class'].queryset = SchoolClass.objects.filter(school=school)
