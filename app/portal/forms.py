from __future__ import annotations

from django import forms
from django.contrib.auth import get_user_model

from .roles import ALL_ROLES


class PortalUserCreateForm(forms.Form):
    username = forms.CharField(max_length=150)
    email = forms.EmailField(required=False)
    password1 = forms.CharField(label="Password", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Confirm password", widget=forms.PasswordInput)

    roles = forms.MultipleChoiceField(
        required=False,
        choices=[(r, r) for r in ALL_ROLES],
        widget=forms.CheckboxSelectMultiple,
        help_text="Assign the user to one or more portal role groups.",
    )

    is_staff = forms.BooleanField(
        required=False,
        help_text="Allows access to Django admin if you also grant permissions.",
    )

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        User = get_user_model()
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("That username is already taken.")
        return username

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("password1")
        p2 = cleaned.get("password2")
        if p1 and p2 and p1 != p2:
            self.add_error("password2", "Passwords do not match.")
        return cleaned
