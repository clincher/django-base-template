# -*- coding: utf-8 -*-
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from apps.users.models import User
from forms import AdminUserChangeForm, AdminUserCreationForm


class CustomUserAdmin(UserAdmin):
    # The forms to add and change user instances
    form = AdminUserChangeForm
    add_form = AdminUserCreationForm

    # The fields to be used in displaying the User model.
    # These override the definitions on the base UserAdmin
    # that reference specific fields on auth.User.
    list_display = ('email', 'get_full_name')
    list_filter = ('is_superuser',)
    # fieldsets = (
    #     ('', {
    #         'fields': ('first_name', 'last_name', 'gender',
    #                    'pastimes', 'url'),
    #     }),
    #     ('Permissions', {
    #         'classes': ('grp-collapse grp-closed',),
    #         'fields': ('is_superuser', 'is_active', 'is_staff', 'groups'),
    #     }),
    #     ('Important dates', {
    #         'classes': ('grp-collapse grp-closed',),
    #         'fields': ('last_login',),
    #     }),
    #     ('Other', {
    #         'classes': ('grp-collapse grp-closed',),
    #         'fields': ('email', 'password'),
    #     })
    # )
    add_fieldsets = (
        (None, {
            'fields': ('email', 'first_name', 'last_name',
                       'password1', 'password2')
        }),
    )
    search_fields = ('email',)
    ordering = ('email',)
    filter_horizontal = ()

    def get_queryset(self, request):
        qs = super(CustomUserAdmin, self).get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(is_staff=False)
        return qs

    def get_readonly_fields(self, request, obj=None):
        fields = self.readonly_fields
        if not request.user.is_superuser:
            fields += ('is_active', 'is_staff', 'is_superuser', 'groups')
        return fields


# Now register the new UserAdmin...
admin.site.register(User, CustomUserAdmin)
# ... and, since we're not using Django's builtin permissions,
# unregister the Group model from admin.
#admin.site.unregister(Group)
