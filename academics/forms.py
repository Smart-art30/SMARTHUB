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
    exam = forms.ModelChoiceField(queryset=Exam.objects.none())
    school_class = forms.ModelChoiceField(queryset=SchoolClass.objects.none())
    subjects = forms.ModelMultipleChoiceField(queryset=Subject.objects.none())

    def __init__(self, *args, **kwargs):
        school = kwargs.pop("school", None)
        super().__init__(*args, **kwargs)

        if school:
            self.fields["exam"].queryset = Exam.objects.filter(school=school)
            self.fields["school_class"].queryset = SchoolClass.objects.filter(school=school)
            self.fields["subjects"].queryset = Subject.objects.filter(school=school)

class ExamForm(forms.ModelForm):
    class Meta:
        model = Exam
        fields = ['name', 'term', 'year']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'term': forms.TextInput(attrs={'class': 'form-control'}),
            'year': forms.NumberInput(attrs={'class': 'form-control', 'min': '2000', 'max': '2030'}),
        }