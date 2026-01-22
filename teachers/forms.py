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

class TeacherSubjectAssignmentForm(forms.Form):
    teacher = forms.ModelChoiceField(queryset=Teacher.objects.none())
    school_class = forms.ModelChoiceField(queryset=SchoolClass.objects.none())
    subject = forms.ModelMultipleChoiceField(
        queryset=Subject.objects.none(),
        widget=forms.CheckboxSelectMultiple  # or SelectMultiple
    )

    def __init__(self, *args, **kwargs):
        school = kwargs.pop('school', None)
        super().__init__(*args, **kwargs)
        if school:
            self.fields['teacher'].queryset = Teacher.objects.filter(school=school)
            self.fields['school_class'].queryset = SchoolClass.objects.filter(school=school)
            self.fields['subject'].queryset = Subject.objects.filter(school=school)
