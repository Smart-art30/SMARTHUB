from django import forms
from .models import Student, SchoolClass
from accounts.models import User

class StudentAddForm(forms.ModelForm):
    user = forms.ModelChoiceField(
        queryset=User.objects.filter(role='student'),
        label="Select Student",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    student_class = forms.ModelChoiceField(
        queryset=SchoolClass.objects.none(),  # We'll set this in the view
        label="Select Class",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    admission_number = forms.CharField(
        max_length=30,
        label="Admission Number",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Student
        fields = ['user', 'admission_number', 'student_class']
