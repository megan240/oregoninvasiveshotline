from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.urls import reverse
from django import forms

from oregoninvasiveshotline.utils.search import SearchForm
from oregoninvasiveshotline.utils.images import generate_thumbnail
from oregoninvasiveshotline.users.models import User


class UserSearchForm(SearchForm):
    is_manager = forms.BooleanField(initial=True, required=False)

    def get_search_fields(self):
        return ('first_name', 'last_name', 'email')

    def search(self, queryset):
        users = super().search(queryset)

        if self.cleaned_data.get('is_manager'):
            users = users.filter(is_active=True)

        return users


class PublicLoginForm(forms.Form):
    """
    Allows users to log in via a link sent via email.
    """
    email = forms.EmailField()

    def __init__(self, request=None, *args, **kwargs):
        super().__init__(*args, **kwargs)


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = (
            'email',
            'first_name',
            'last_name',
            'phone',
            'biography',
            'affiliations',
            'photo',
            'is_active',
            'is_staff',
        )

    def __init__(self, *args, **kwargs):
        """
        `user` is the person using the form, not the person the form is actually going edit
        """
        user = kwargs.pop('user')

        super().__init__(*args, **kwargs)

        # add a password field to the form if the user is being created. This
        # allows an admin to set an initial password
        if self.instance.pk is None:
            self.fields['password'] = forms.CharField(widget=forms.widgets.PasswordInput)

        if user.pk == self.instance.pk:
            # these fields you shouldn't be allowed to alter if you're editing
            # yourself, for safety reasons
            self.fields.pop("is_active")
            self.fields.pop("is_staff")

        if not user.is_staff:
            # only staff members can control the is_staff field
            self.fields.pop("is_staff", None)

        # only active users should be allowed to fill out these fields
        if not user.is_active:
            self.fields.pop("photo")
            self.fields.pop("biography")
            self.fields.pop("affiliations")

        # stupid chrome...http://stackoverflow.com/a/30976223/2733517
        for name, field in self.fields.items():
            field.widget.attrs['autocomplete'] = "new-password"

    def save(self, *args, **kwargs):
        """
        Save the form, and set the password, if it has been set
        """
        password = self.cleaned_data.pop("password", None)
        if password is not None:
            self.instance.set_password(password)

        instance = super().save(*args, **kwargs)

        # if we got a new photo resize it and convert it to a png (why????????????????????)
        """
        if self.cleaned_data.get("photo"):
            output_path = instance.photo.path + ".png"
            generate_thumbnail(instance.photo.path, output_path, width=256, height=256)
            self.instance.photo = instance.photo.name + ".png"
            self.instance.save()

        return instance
        """
        