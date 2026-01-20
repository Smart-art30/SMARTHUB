from django import forms
from .models import Subject

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
