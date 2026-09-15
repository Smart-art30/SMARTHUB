
from django import forms
from .models import Subject, Exam, AcademicTerm
from schools.models import SchoolClass


class SubjectForm(forms.ModelForm):

    class Meta:
        model = Subject
        fields = ["name", "code"]

    def __init__(self, *args, **kwargs):
        self.school = kwargs.pop("school", None)
        super().__init__(*args, **kwargs)

    def clean_code(self):
        code = self.cleaned_data["code"]

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

    exam = forms.ModelChoiceField(
        queryset=Exam.objects.none()
    )

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
            self.fields["exam"].queryset = Exam.objects.filter(
                school=school
            )

            self.fields["school_class"].queryset = SchoolClass.objects.filter(
                school=school
            )

            self.fields["subjects"].queryset = Subject.objects.filter(
                school=school
            )


class ExamForm(forms.ModelForm):

    year = forms.ChoiceField(
        label="Year",
        required=True,
        choices=[
            ("", "Select Year")
        ] + [
            (str(year), str(year))
            for year in range(2020, 2090)
        ],
        widget=forms.Select(
            attrs={
                "class": "form-select",
                "id": "id_year",
            }
        ),
    )

    class Meta:

        model = Exam

        fields = [
            "name",
            "exam_type",
            "year",
            "term",
        ]

        widgets = {

            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter exam name",
                }
            ),

            "exam_type": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),

            "term": forms.Select(
                attrs={
                    "class": "form-select",
                    "id": "id_term",
                }
            ),
        }

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        # -----------------------------------------------------
        # TERMS ARE UNIVERSAL
        # -----------------------------------------------------
        self.fields["term"].queryset = AcademicTerm.objects.all()

        # -----------------------------------------------------
        # EDITING EXISTING EXAM
        # -----------------------------------------------------
        if self.instance.pk:

            self.fields["year"].initial = str(
                self.instance.year
            )

            self.fields["term"].initial = (
                self.instance.term_id
            )
