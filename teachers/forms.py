from django import forms
from .models import Teacher
from .models import TeacherSubjectAssignment
from academics.models import Subject
from academics.models import Subject, SchoolClass
from django import forms
from .models import Teacher
from django.contrib.auth import get_user_model

User = get_user_model()

class TeacherAdminForm(forms.ModelForm):
   
    first_name = forms.CharField(max_length=150, required=True)
    last_name = forms.CharField(max_length=150, required=True)
    email = forms.EmailField(required=True)

    class Meta:
        model = Teacher
        fields = [
            'first_name', 'last_name', 'email', 
            'employee_id',
            'phone',
            'designation',
            'qualification',
            'specialization',
            'date_of_birth',
            'gender',
            'profile_picture'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
      
        if self.instance and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email

    def save(self, commit=True):
        teacher = super().save(commit=False)
       
        teacher.user.first_name = self.cleaned_data['first_name']
        teacher.user.last_name = self.cleaned_data['last_name']
        teacher.user.email = self.cleaned_data['email']
        if commit:
            teacher.user.save()
            teacher.save()
        return teacher



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
    teacher = forms.ModelChoiceField(
        queryset=Teacher.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    school_class = forms.ModelChoiceField(
        queryset=SchoolClass.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    subject = forms.ModelMultipleChoiceField(
        queryset=Subject.objects.none(),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'})
    )

    def __init__(self, *args, **kwargs):
        school = kwargs.pop('school', None)
        super().__init__(*args, **kwargs)
        if school:
            self.fields['teacher'].queryset = Teacher.objects.filter(school=school)
            self.fields['school_class'].queryset = SchoolClass.objects.filter(school=school)
            self.fields['subject'].queryset = Subject.objects.filter(school=school)