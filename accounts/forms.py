from django import forms
from django.contrib.auth import get_user_model
from schools.models import School

User = get_user_model()

class UserRegistrationForm(forms.ModelForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control rounded-3',
            'placeholder': 'Username'
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control rounded-3',
            'placeholder': 'Email'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control rounded-3',
            'placeholder': 'Password'
        })
    )
    password2 = forms.CharField(
        label='Confirm password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control rounded-3',
            'placeholder': 'Confirm Password'
        })
    )
    school = forms.ModelChoiceField(
        queryset=School.objects.all(),
        empty_label="Select your school",
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-select rounded-3'
        })
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'role', 'school']

    def clean_password2(self):
        cd = self.cleaned_data
        if cd.get('password') != cd.get('password2'):
            raise forms.ValidationError("Passwords don’t match.")
        return cd['password2']
