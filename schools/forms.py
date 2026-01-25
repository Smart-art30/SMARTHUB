from django import forms
from .models import School, SchoolClass
from academics.models import Subject

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
