import base64
import binascii
from datetime import datetime, timedelta
from urllib import parse

from django.contrib.auth.models import AbstractBaseUser, UserManager
from django.contrib.sites.models import Site
from django.core.signing import TimestampSigner, SignatureExpired
from django.urls import reverse
from django.db import models

from oregoninvasiveshotline.utils.urls import build_absolute_url


class User(AbstractBaseUser):

    class Meta:
        db_table = 'user'
        ordering = ['first_name', 'last_name']

    USERNAME_FIELD = 'email'

    objects = UserManager()

    user_id = models.AutoField(primary_key=True)
    email = models.EmailField(max_length=255, unique=True)
    first_name = models.CharField(max_length=255, null=True)
    last_name = models.CharField(max_length=255, null=True)
    phone = models.CharField(max_length=255, default="", blank=True)
    prefix = models.CharField(max_length=255)
    suffix = models.CharField(max_length=255)
    date_joined = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True, blank=True, verbose_name="Is Manager (can login and manage reports)")
    is_staff = models.BooleanField(default=False, blank=True, verbose_name="Is Admin (can do anything)")
    affiliations = models.TextField(blank=True)
    biography = models.TextField(blank=True)
    photo = models.ImageField(upload_to="images", blank=True)
    has_completed_ofpd = models.BooleanField(default=False, blank=True, verbose_name="""
        Check this box if you have completed the Oregon
        Forest Pest Detector training, offered by Oregon State
        Extension.""")

    @classmethod
    def from_signature(cls, signature):
        try:
            signer = TimestampSigner()
            value = signer.unsign(signature, max_age=60 * 60 * 24 * 7)
            return cls.objects.get(email=value)
        except SignatureExpired:
            return None
        except binascii.Error:
            # Typically, this would indicate a non-base64-encoded value
            return None

    def get_authentication_url(self, next=None):
        signer = TimestampSigner()
        return build_absolute_url(
            reverse('users-authenticate'),
            parse.urlencode({
                'sig': signer.sign(self.email),
                'next': next or '',
            }))

    @property
    def full_name(self):
        """A nicer way to get the user's full name."""
        return self.get_full_name()

    def get_full_name(self):
        if self.first_name:
            name = self.first_name
            if self.last_name:
                name = '{name} {self.last_name}'.format_map(locals())
            return name
        return self.email

    def get_short_name(self):
        if self.first_name:
            name = self.first_name
            if self.last_name:
                last_initial = self.last_name[0]
                name = '{name} {last_initial}.'.format_map(locals())
            return name
        return self.email

    def get_proper_name(self):
        if self.first_name:
            parts = (self.prefix, self.first_name, self.last_name)
            name = ' '.join(p for p in parts if p)
            if self.suffix:
                name = '{name}, {self.suffix}'.format_map(locals())
            return name
        return self.email

    def get_avatar_url(self):
        if self.photo:
            return self.photo.url
        return reverse("users-avatar", args=[self.pk])

    # we don't need granular permissions; all staff will have access to
    # everything
    def has_perm(self, perm, obj=None):
        return self.is_staff

    def has_module_perms(self, app_label):
        return self.is_staff

    def __str__(self):
        return self.get_full_name()
