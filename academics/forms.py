from django import forms
from .models import Subject
from schools.models import SchoolClass
from .models import Exam
from django import forms
from .models import Exam, AcademicTerm

class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['name', 'code']

    def __init__(self, *args, **kwargs):
        self.school = kwargs.pop('school', None)
        super().__init__(*args, **kwargs)

    def clean_code(self):
        code = self.cleaned_data['code']

        qs = Subject.objects.filter(
            school=self.school,
            code__iexact=code
        )

        
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise forms.ValidationError(
                "A subject with this code already exists in your school."
            )

        return code


class AssignSubjectsToExamForm(forms.Form):
    exam = forms.ModelChoiceField(queryset=Exam.objects.none())

    school_class = forms.ModelMultipleChoiceField(
        queryset=SchoolClass.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=True
    )

    subjects = forms.ModelMultipleChoiceField(
        queryset=Subject.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=True
    )

    def __init__(self, *args, **kwargs):
        school = kwargs.pop("school", None)
        super().__init__(*args, **kwargs)

        if school:
            self.fields["exam"].queryset = Exam.objects.filter(school=school)
            self.fields["school_class"].queryset = SchoolClass.objects.filter(school=school)
            self.fields["subjects"].queryset = Subject.objects.filter(school=school)


class ExamForm(forms.ModelForm):
    year = forms.IntegerField(
        label='Year',
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'readonly': True})
    )

    class Meta:
        model = Exam
        fields = ['name', 'exam_type', 'term', 'year']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'exam_type': forms.Select(attrs={'class': 'form-control'}),
            'term': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        school = kwargs.pop('school', None)
        super().__init__(*args, **kwargs)

        if school:
            terms = AcademicTerm.objects.filter(school=school).order_by('-year', 'term')
            self.fields['term'].queryset = terms
            self.term_year_map = {str(term.id): term.year for term in terms}

        if self.instance and getattr(self.instance, 'term_id', None):
            self.fields['year'].initial = self.instance.term.year

        term_id = self.data.get('term')
        if term_id:
            term = AcademicTerm.objects.filter(id=term_id).first()
            if term:
                self.fields['year'].initial = term.year

    def save(self, commit=True):
        exam = super().save(commit=False)
        if self.cleaned_data.get('term'):
            exam.year = self.cleaned_data['term'].year
        if commit:
            exam.save()
        return exam