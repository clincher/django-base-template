from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import UpdateView
from django.views.generic.detail import SingleObjectMixin

from braces.views import SuccessURLRedirectListMixin
from apps.users.forms import UserForm


class CustomUserObjectMixin(SingleObjectMixin):
    """
    Provides views with the current user's profile.
    """
    model = get_user_model()

    def get_object(self, queryset=None):
        """
        Returns the current users profile.
        """
        try:
            return self.request.user
        except self.model.DoesNotExist:
            raise NotImplemented(
                "What if the user doesn't have an associated profile?")

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        """Ensures that only authenticated users can access the view."""
        klass = CustomUserObjectMixin
        return super(klass, self).dispatch(request, *args, **kwargs)


class UserUpdateView(CustomUserObjectMixin,
                     SuccessURLRedirectListMixin,
                     UpdateView):
    """
    A view that displays a form for editing a user's profile.

    Uses a form dynamically created for the `CustomUser` model and
    the default model's update template.
    """
    form_class = UserForm
    success_list_url = "user_update"
