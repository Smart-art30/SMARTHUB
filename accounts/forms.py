from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from schools.models import School

User = get_user_model()


class UserRegistrationForm(forms.ModelForm):

    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control rounded-3",
                "placeholder": "Password",
                "autocomplete": "new-password",
            }
        ),
        validators=[validate_password],
    )

    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control rounded-3",
                "placeholder": "Confirm Password",
                "autocomplete": "new-password",
            }
        ),
    )

    school = forms.ModelChoiceField(
        queryset=School.objects.all(),
        empty_label="Select your school",
        required=True,
        widget=forms.Select(
            attrs={
                "class": "form-select rounded-3"
            }
        ),
    )

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "role",
            "school",
        ]

        widgets = {
            "username": forms.TextInput(
                attrs={
                    "class": "form-control rounded-3",
                    "placeholder": "Username",
                    "autocomplete": "username",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": "form-control rounded-3",
                    "placeholder": "Email",
                    "autocomplete": "email",
                }
            ),
            "role": forms.Select(
                attrs={
                    "class": "form-select rounded-3"
                }
            ),
        }

    def clean_username(self):
        username = self.cleaned_data["username"].strip()

        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError(
                "A user with this username already exists."
            )

        return username

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()

        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "An account with this email already exists."
            )

        return email

    def clean_password2(self):
        password = self.cleaned_data.get("password")
        password2 = self.cleaned_data.get("password2")

        if password and password2 and password != password2:
            raise forms.ValidationError(
                "Passwords don't match."
            )

        return password2

    def save(self, commit=True):
        user = super().save(commit=False)

        user.username = self.cleaned_data["username"]
        user.email = self.cleaned_data["email"]
        user.school = self.cleaned_data["school"]

        user.set_password(self.cleaned_data["password"])

        if commit:
            user.save()

        return user