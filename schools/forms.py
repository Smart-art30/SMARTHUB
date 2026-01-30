from django import forms
from .models import School, SchoolClass
from academics.models import Subject
from academics.models import Exam

class SchoolSignupForm(forms.ModelForm):
    admin_email = forms.EmailField()
    admin_password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = School
        fields = ['name','code','address']


class SchoolClassForm(forms.ModelForm):
    class Meta:
        model = SchoolClass
        fields = ['name', 'stream', 'section', 'subjects']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if user and hasattr(user, 'school'):
            qs = Subject.objects.filter(school=user.school)
            self.fields['subjects'].queryset = qs
            print("DEBUG subjects queryset:", list(qs)) 

        self.fields['subjects'].widget = forms.CheckboxSelectMultiple()



class AssignExamForm(forms.Form):
    exam = forms.ModelChoiceField(queryset=Exam.objects.none())
    classes = forms.ModelMultipleChoiceField(
        queryset=SchoolClass.objects.none(),
        widget=forms.CheckboxSelectMultiple
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if user and hasattr(user, 'school'):
           
            self.fields['exam'].queryset = Exam.objects.filter(school=user.school)
            self.fields['classes'].queryset = SchoolClass.objects.filter(school=user.school)