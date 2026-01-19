from django import forms
from .models import Teacher

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
