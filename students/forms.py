from django import forms
from .models import Student
from schools.models import SchoolClass, School
from django.contrib.auth import get_user_model

User = get_user_model()

class StudentAddForm(forms.ModelForm):
    user = forms.ModelChoiceField(
        queryset=User.objects.filter(role='student'),
        label="Select Student",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    school = forms.ModelChoiceField(
        queryset=School.objects.all(),
        label="Select School",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    student_class = forms.ModelChoiceField(
        queryset=SchoolClass.objects.none(),  # We'll set this dynamically
        label="Select Class",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    admission_number = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    date_of_birth = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    gender = forms.ChoiceField(
        choices=(('male','Male'), ('female','Female')),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    photo = forms.ImageField(
        required=False,
        widget=forms.ClearableFileInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Student
        fields = ['user','school','student_class','admission_number','date_of_birth','gender','photo']
