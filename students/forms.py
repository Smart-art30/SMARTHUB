from django import forms
from .models import Student
from schools.models import SchoolClass, School
from django.contrib.auth import get_user_model
from .models import Parent

User = get_user_model()


class StudentAddForm(forms.ModelForm):
    # Add first_name and last_name from User
    first_name = forms.CharField(
        max_length=150,
        label="First Name",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        max_length=150,
        label="Last Name",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    school = forms.ModelChoiceField(
        queryset=School.objects.all(),
        label="Select School",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    student_class = forms.ModelChoiceField(
        queryset=SchoolClass.objects.none(),
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
        fields = [
            'first_name', 'last_name',
            'school', 'student_class', 'admission_number',
            'date_of_birth', 'gender', 'photo'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Populate first_name and last_name from related User
        if self.instance and self.instance.pk:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name

        # Populate class dropdown based on school
        if self.instance and self.instance.school:
            self.fields['student_class'].queryset = SchoolClass.objects.filter(
                school=self.instance.school
            )
        else:
            self.fields['student_class'].queryset = SchoolClass.objects.none()

    def save(self, commit=True):
        # Save Student instance
        student = super().save(commit=False)

        # Save User fields
        student.user.first_name = self.cleaned_data['first_name']
        student.user.last_name = self.cleaned_data['last_name']
        if commit:
            student.user.save()
            student.save()
        return student

class ParentForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)
    email = forms.EmailField()

    class Meta:
        model = Parent
        fields = ['phone', 'students', 'first_name', 'last_name', 'email']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email

    def save(self, commit=True):
        parent = super().save(commit=False)
        user = parent.user
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            parent.save()
            self.save_m2m()
        return parent