
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

    # ---------------------------------------------------------
    # YEAR
    # ---------------------------------------------------------
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

    # ---------------------------------------------------------
    # META
    # ---------------------------------------------------------
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

    # ---------------------------------------------------------
    # INITIALIZATION
    # ---------------------------------------------------------
    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        # Terms are universal.
        #
        # We initially leave the queryset empty.
        # It will be populated based on the selected year.
        self.fields["term"].queryset = AcademicTerm.objects.none()

        # -----------------------------------------------------
        # EDITING AN EXISTING EXAM
        # -----------------------------------------------------
        if self.instance.pk and self.instance.term_id:

            term = self.instance.term

            # Get the year from the existing term
            self.fields["year"].initial = str(term.year)

            # Load all universal terms for that year
            self.fields["term"].queryset = AcademicTerm.objects.filter(
                year=term.year
            ).order_by("term")

            # Keep the current term selected
            self.fields["term"].initial = term.pk

        # -----------------------------------------------------
        # FORM SUBMITTED / POST REQUEST
        # -----------------------------------------------------
        elif self.data.get("year"):

            try:

                year = int(self.data.get("year"))

                # Load universal terms for submitted year
                self.fields["term"].queryset = AcademicTerm.objects.filter(
                    year=year
                ).order_by("term")

            except (TypeError, ValueError):

                pass

    # ---------------------------------------------------------
    # VALIDATION
    # ---------------------------------------------------------
    def clean(self):

        cleaned_data = super().clean()

        year = cleaned_data.get("year")
        term = cleaned_data.get("term")

        # Make sure both were selected
        if year and term:

            try:

                year = int(year)

            except (TypeError, ValueError):

                self.add_error(
                    "year",
                    "Invalid academic year."
                )

                return cleaned_data

            # Make sure the selected term belongs
            # to the selected year.
            if term.year != year:

                self.add_error(
                    "term",
                    "The selected term does not belong "
                    "to the selected year."
                )

        return cleaned_data
