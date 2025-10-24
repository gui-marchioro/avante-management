from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


def validate_password_strength(value: str) -> None:
    if len(value) < 8:
        raise ValidationError(
            'Password must be at least 8 characters long.',
            code='invalid'
        )
    if not any(char.isdigit() for char in value):
        raise ValidationError(
            'Password must contain at least one numeral.',
            code='invalid'
        )
    if not any(char.isalpha() for char in value):
        raise ValidationError(
            'Password must contain at least one letter.',
            code='invalid'
        )
    if not any(char.isupper() for char in value):
        raise ValidationError(
            'Password must contain at least one uppercase letter.',
            code='invalid'
        )
    if not any(char.islower() for char in value):
        raise ValidationError(
            'Password must contain at least one lowercase letter.',
            code='invalid'
        )


class RegisterForm(forms.ModelForm):  # type: ignore
    password = forms.CharField(
        required=True, widget=forms.PasswordInput, label='Senha',
        validators=[validate_password_strength]
    )
    password2 = forms.CharField(
        required=True, widget=forms.PasswordInput, label='Confirmar senha'
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email']

    def clean(self):
        cleaned_data = super().clean()

        password = cleaned_data.get('password')
        password2 = cleaned_data.get('password2')

        if password != password2:
            password_confirmation_error = ValidationError(
                'Passwords must be equal',
                code='invalid'
            )
            raise ValidationError({
                'password': password_confirmation_error,
                'password2': password_confirmation_error,
            })

    def save(self, commit: bool = True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user
