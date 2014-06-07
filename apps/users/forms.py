# -*- coding: utf-8 -*-
from django.forms import ModelForm
from django import forms
from django.utils.translation import ugettext_lazy as _
from django.utils.text import capfirst
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.models import UserManager

from braces.views import FormValidMessageMixin


class UserForm(FormValidMessageMixin, ModelForm):
    form_valid_message = _(u"Account updated!")
    success_list_url = "user_update"
    class Meta:
        model = get_user_model()
        exclude = [
            'password',
            'email',
            'is_staff',
            'is_active',
            'date_joined',
            'last_login',
            'groups',
            'is_superuser',
            'user_permissions'
        ]


class CleanEmailMixin:
    def clean_email(self):
        return UserManager.normalize_email(self.cleaned_data["email"])


class EmailAuthenticateForm(CleanEmailMixin, forms.Form):
    """
    Base class for authenticating users. Extend this to get a form that accepts
    username/password logins.
    """
    email = forms.EmailField(max_length=255)
    password = forms.CharField(label=_("Пароль"), widget=forms.PasswordInput)

    error_messages = {
        'invalid_login': _("Пожалуйста, проверьте правильность ввода "
                           "электронной почты и пароля. "
                           "Обратите внимание на то, что оба поля "
                           "чувствительны к регистру."),
        'no_cookies': _("Your Web browser doesn't appear to have cookies "
                        "enabled. Cookies are required for logging in."),
        'inactive': _("Акаунт не активирован."),
    }

    def __init__(self, request=None, *args, **kwargs):
        """
        If request is passed in, the form will validate that cookies are
        enabled. Note that the request (a HttpRequest object) must have set a
        cookie with the key TEST_COOKIE_NAME and value TEST_COOKIE_VALUE before
        running this validation.
        """
        self.request = request
        self.user_cache = None
        super(EmailAuthenticateForm, self).__init__(*args, **kwargs)

        # Set the label for the "username" field.
        UserModel = get_user_model()
        email_field = UserModel._meta.get_field(UserModel.EMAIL_FIELD)
        self.fields[UserModel.EMAIL_FIELD].label = capfirst(
            email_field.verbose_name)

    def clean(self):
        email = self.cleaned_data.get('email')
        password = self.cleaned_data.get('password')

        if email and password:
            self.user_cache = authenticate(email=email, password=password)
            if self.user_cache is None:
                raise forms.ValidationError(
                    self.error_messages['invalid_login'])
            elif not self.user_cache.is_active:
                raise forms.ValidationError(self.error_messages['inactive'])
        self.check_for_test_cookie()
        return self.cleaned_data

    def check_for_test_cookie(self):
        if self.request and not self.request.session.test_cookie_worked():
            raise forms.ValidationError(self.error_messages['no_cookies'])

    def get_user_id(self):
        if self.user_cache:
            return self.user_cache.id
        return None

    def get_user(self):
        return self.user_cache


class RegistrationForm(CleanEmailMixin, forms.ModelForm):
    """
    A form that creates a user, with no privileges, from the given email and
    password.
    """
    error_messages = {
        'duplicate_email': _("Плоьзователь с таким именем уже существует."),
        'password_mismatch': _("Пароли не совпадают."),
    }
    password1 = forms.CharField(label=_("Пароль"), widget=forms.PasswordInput)
    password2 = forms.CharField(
        label=_("Подтверждение пароля"), widget=forms.PasswordInput,
        help_text=_("Введите еще раз тот же пароль для проверки."))

    class Meta:
        model = get_user_model()
        fields = ("email",)

    def clean_email(self):
        # Since User.username is unique, this check is redundant,
        # but it sets a nicer error message than the ORM. See #13147.
        email = super(RegistrationForm, self).clean_email()
        User = get_user_model()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(self.error_messages['duplicate_email'])

        return email

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(
                self.error_messages['password_mismatch'])
        return password2

    def save(self, commit=True):
        user = super(RegistrationForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class AdminUserCreationForm(CleanEmailMixin, forms.ModelForm):
    """A form for creating new users. Includes all the required
    fields, plus a repeated password."""
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(
        label='Password confirmation', widget=forms.PasswordInput)

    class Meta:
        model = get_user_model()
        excludes = ('residence', 'timezone', 'bio', 'is_staff', 'is_active')

    def clean_password2(self):
        # Check that the two password entries match
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2

    def save(self, commit=True):
        # Save the provided password in hashed format
        user = super(AdminUserCreationForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class AdminUserChangeForm(CleanEmailMixin, forms.ModelForm):
    """A form for updating users. Includes all the fields on
    the user, but replaces the password field with admin's
    password hash display field.
    """
    password = ReadOnlyPasswordHashField()

    class Meta:
        model = get_user_model()

    def clean_password(self):
        # Regardless of what the user provides, return the initial value.
        # This is done here, rather than on the field, because the
        # field does not have access to the initial value
        return self.initial["password"]
