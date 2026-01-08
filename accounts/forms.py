from django import forms
from django.contrib.auth import get_user_model
from schools.models import School


User = get_user_model()

class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirm password', widget=forms.PasswordInput)
    school = forms.ModelChoiceField(
        queryset=School.objects.all(),
        empty_label="Select your school",
        required=True
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'role']

    def clean_password2(self):
        cd = self.cleaned_data
        if cd['password'] != cd['password2']:
            raise forms.ValidationError("Passwords don’t match.")
        return cd['password2']
