import tempfile
from base64 import b64decode
from unittest.mock import patch

from django import forms
from django.contrib.gis.geos import Point
from django.forms.models import modelformset_factory
from django.test import TestCase

from model_bakery.baker import make

from oregoninvasiveshotline.utils.test.user import UserMixin
from oregoninvasiveshotline.reports.models import Report

from .fields import ClearableImageInput
from .forms import BaseImageFormSet, ImageForm, get_image_formset
from .models import Image


ORIGIN = Point(0, 0)


class ImageFormTest(TestCase, UserMixin):
    def test_visibility_field_removed(self):
        user = self.create_user(username="foo@example.com")
        form = ImageForm()
        self.assertNotIn("visibility", form.fields)
        with patch("oregoninvasiveshotline.images.forms.can_adjust_visibility", return_value=False):
            form = ImageForm(user=user)
            self.assertNotIn("visibility", form.fields)

        with patch("oregoninvasiveshotline.images.forms.can_adjust_visibility", return_value=True):
            form = ImageForm(user=user)
            self.assertIn("visibility", form.fields)


class BaseImageFormSetTest(TestCase, UserMixin):
    def test_user_and_fk_gets_passed_to_save_new(self):
        ImageFormSet = modelformset_factory(Image, form=ImageForm, formset=BaseImageFormSet, can_delete=True)
        formset = ImageFormSet({
            "form-TOTAL_FORMS": "1",
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            "form-0-image_data_uri": "data:image/gif;base64,R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
            "form-0-name": "Hello world",
        })
        self.assertTrue(formset.is_valid())
        report = make(Report, point=ORIGIN)
        user = self.create_user(username="foo@example.com")
        formset.save(fk=report, user=user)
        self.assertEqual(Image.objects.filter(report=report, created_by=user).count(), 1)


class GetImageFormSetTest(TestCase, UserMixin):
    def test(self):
        user = self.create_user(username="admin@example.com", is_staff=True)
        ImageFormSet = get_image_formset(user=user)
        formset = ImageFormSet({
            "form-TOTAL_FORMS": "1",
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            "form-0-image_data_uri": "data:image/gif;base64,R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
            "form-0-name": "Hello world",
            "form-0-visibility": Image.PUBLIC,
        })
        self.assertTrue(formset.is_valid())
        report = make(Report, point=ORIGIN)
        formset.save(fk=report, user=user)
        self.assertEqual(Image.objects.filter(report=report, created_by=user, visibility=Image.PUBLIC).count(), 1)


class ClearableImageInputTest(TestCase):
    def setUp(self):
        class Form(forms.Form):
            image = forms.ImageField(widget=ClearableImageInput)
            name = forms.CharField()

        self.Form = Form
        self.b64 = "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs="
        self.other_b64 = "R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw=="

    def test_normal_file_upload(self):
        f = tempfile.TemporaryFile()
        f.write(b64decode(self.b64))
        f.flush()
        f.seek(0)

        form = self.Form({"name": "hi"}, {"image": f})
        self.assertTrue(form.is_valid())

    def test_data_uri_upload(self):
        img_uri = "data:image/gif;base64," + self.b64
        form = self.Form({"name": "hi", "image_data_uri": img_uri})
        self.assertTrue(form.is_valid())

    def test_file_preserved_on_error(self):
        img_uri = "data:image/gif;base64," + self.b64
        form = self.Form({"name": "", "image_data_uri": img_uri})
        self.assertFalse(form.is_valid())
        signed_path = form.fields['image'].widget.signed_path

        form = self.Form({"name": "hello", "image_signed_path": signed_path})
        self.assertTrue(form.is_valid())

    def test_invalid_signed_path(self):
        img_uri = "data:image/gif;base64," + self.b64
        form = self.Form({"name": "", "image_data_uri": img_uri})
        self.assertFalse(form.is_valid())

        form = self.Form({"name": "hello", "image_signed_path": "asdf"})
        self.assertFalse(form.is_valid())

    def test_invalid_data_uri(self):
        img_uri = "invalid"
        form = self.Form({"name": "hello", "image_data_uri": img_uri})
        self.assertFalse(form.is_valid())

    def test_whole_sequence(self):
        # post invalid data
        img_uri = "invalid"
        form = self.Form({"name": "", "image_data_uri": img_uri})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.fields['image'].widget.signed_path, None)

        # post a valid image
        img_uri = "data:image/gif;base64," + self.b64
        form = self.Form({"name": "", "image_data_uri": img_uri})
        self.assertFalse(form.is_valid())
        signed_path = form.fields['image'].widget.signed_path
        self.assertIn(signed_path, str(form))

        # post the signed_path back
        form = self.Form({"name": "hello", "image_signed_path": signed_path})
        self.assertTrue(form.is_valid())

        # post a new image
        img_uri = "data:image/gif;base64," + self.other_b64
        form = self.Form({"name": "hello", "image_signed_path": signed_path, "image_data_uri": img_uri})
        self.assertTrue(form.is_valid())
        self.assertNotEqual(signed_path, form.fields['image'].widget.signed_path)
        self.assertEqual(open(form.fields['image'].widget.signed_path.split(":")[0], 'rb').read(), b64decode(self.other_b64))
