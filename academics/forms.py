from django import forms
from .models import Subject
from schools.models import SchoolClass
from .models import Exam

class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['name', 'code']

    def __init__(self, *args, **kwargs):
        self.school = kwargs.pop('school', None)
        super().__init__(*args, **kwargs)

    def clean_code(self):
        code = self.cleaned_data['code']

        if Subject.objects.filter(
            school=self.school,
            code__iexact=code
        ).exists():
            raise forms.ValidationError(
                "A subject with this code already exists in your school."
            )

        return code



class AssignSubjectsToExamForm(forms.Form):
    exam = forms.ModelChoiceField(queryset=Exam.objects.all(), required=True)
    school_class = forms.ModelChoiceField(queryset=SchoolClass.objects.all(), required=True)
    subjects = forms.ModelMultipleChoiceField(queryset=Subject.objects.all(), widget=forms.CheckboxSelectMultiple)