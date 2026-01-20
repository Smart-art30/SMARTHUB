from django import forms
from .models import Teacher
from .models import TeacherSubjectAssignment

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



class TeacherSubjectAssignmentForm(forms.ModelForm):
    class Meta:
        model = TeacherSubjectAssignment
        fields = ['teacher', 'school_class', 'subject']
        widgets = {
            'teacher': forms.Select(attrs={'class': 'form-select'}),
            'school_class': forms.Select(attrs={'class': 'form-select'}),
            'subject': forms.Select(attrs={'class': 'form-select'}),
        }
