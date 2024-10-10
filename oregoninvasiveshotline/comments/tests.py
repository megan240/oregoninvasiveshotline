from unittest.mock import Mock

from django.core import mail
from django.contrib.gis.geos import Point
from django.test import TestCase, TransactionTestCase
from django.db import transaction
from django.urls import reverse

from model_bakery.baker import make

from oregoninvasiveshotline.utils.test.user import UserMixin
from oregoninvasiveshotline.images.models import Image
from oregoninvasiveshotline.reports.models import Invite, Report

from .forms import CommentForm
from .models import Comment


ORIGIN = Point(0, 0)


class CommentFormTest(TransactionTestCase, UserMixin):

    def setUp(self):
        self.user = self.create_user(
            username="foo@example.com",
            password="foo",
            is_active=True,
            is_staff=False
        )
        self.admin = self.create_user(
            username="admin@example.com",
            password="admin",
            is_active=True,
            is_staff=True
        )
        self.inactive_user = self.create_user(
            username="inactive@example.com",
            is_active=False
        )

    def test_report_and_created_by_initialized_for_new_comment(self):
        report = make(Report, point=ORIGIN)
        form = CommentForm(user=self.user, report=report)
        self.assertEqual(form.instance.created_by, self.user)
        self.assertEqual(form.instance.report, report)

    def test_visibility_field_removed_for_non_experts(self):
        report = make(Report, point=ORIGIN)
        form = CommentForm(user=self.inactive_user, report=report)
        self.assertNotIn("visibility", form.fields)
        self.assertEqual(form.instance.visibility, Comment.PROTECTED)

    def test_emails_sent_out_for_new_comments_notifies_managers_and_staffers_who_commented(self):
        other_user = self.create_user(username="other@example.com", is_active=False)
        report = make(Report, point=ORIGIN)

        should_be_notified = make(Comment, report=report, created_by=self.admin).created_by.email
        should_not_be_notified = make(Comment, report=report, created_by=self.inactive_user).created_by.email
        form = CommentForm({'body': "foo"}, user=other_user, report=report)
        self.assertTrue(form.is_valid())

        # notification task is out-of-band and uses 'on_commit' barrier
        # so the path being tested is wrapped in a transaction
        with transaction.atomic():
            form.save()

        self.assertIn(should_be_notified, [email.to[0] for email in mail.outbox])
        self.assertNotIn(should_not_be_notified, [email.to for email in mail.outbox])

    def test_email_sent_out_for_new_comment_to_user_who_claimed_report(self):
        report = make(Report, claimed_by=self.user, point=ORIGIN)

        form = CommentForm({'body': "foo"}, user=self.inactive_user, report=report)
        self.assertTrue(form.is_valid())

        # notification task is out-of-band and uses 'on_commit' barrier
        # so the path being tested is wrapped in a transaction
        with transaction.atomic():
            form.save()

        self.assertIn(report.claimed_by.email, [email.to[0] for email in mail.outbox])

    def test_email_sent_out_for_new_comment_to_all_invited_experts(self):
        report = make(Report, point=ORIGIN)
        invite = make(Invite, report=report, user=self.user)

        form = CommentForm({'body': "foo"}, user=self.inactive_user, report=report)
        self.assertTrue(form.is_valid())

        # notification task is out-of-band and uses 'on_commit' barrier
        # so the path being tested is wrapped in a transaction
        with transaction.atomic():
            form.save()

        self.assertIn(invite.user.email, [email.to[0] for email in mail.outbox])

    def test_email_not_sent_to_person_submitting_comment(self):
        report = make(Report, point=ORIGIN)
        make(Invite, report=report, user=self.user)

        form = CommentForm({'body': "foo", 'visibility': Comment.PUBLIC},
                           user=self.user, report=report)
        self.assertTrue(form.is_valid())

        # notification task is out-of-band and uses 'on_commit' barrier
        # so the path being tested is wrapped in a transaction
        with transaction.atomic():
            form.save()

        self.assertNotIn(self.user.email, [email.to[0] for email in mail.outbox])

    def test_email_only_sent_to_submitter_if_comment_is_PUBLIC_or_PROTECTED(self):
        report = make(Report, created_by=self.inactive_user, point=ORIGIN)
        invite = make(Invite, report=report)

        form = CommentForm({'body': "foo", 'visibility': Comment.PUBLIC},
                           user=invite.user, report=report)
        self.assertTrue(form.is_valid())

        # notification task is out-of-band and uses 'on_commit' barrier
        # so the path being tested is wrapped in a transaction
        with transaction.atomic():
            form.save()

        self.assertIn(self.inactive_user.email, [email.to[0] for email in mail.outbox])

        mail.outbox = []
        # if the comment is PRIVATE, they don't get notified
        other_user = self.create_user(username="other@example.com", is_active=False)
        report = make(Report, created_by=other_user, point=ORIGIN)
        invite = make(Invite, report=report)

        form = CommentForm({
            'body': "foo",
            'visibility': Comment.PRIVATE,
        }, user=invite.user, report=report)
        self.assertTrue(form.is_valid())

        # notification task is out-of-band and uses 'on_commit' barrier
        # so the path being tested is wrapped in a transaction
        with transaction.atomic():
            form.save()

        self.assertNotIn(other_user.email, [email.to[0] for email in mail.outbox])


class CommentEditViewTest(TestCase, UserMixin):

    def setUp(self):
        self.user = self.create_user(
            username="foo@example.com",
            password="foo",
            is_active=True,
            is_staff=False
        )
        self.admin = self.create_user(
            username="admin@example.com",
            password="admin",
            is_active=True,
            is_staff=True
        )
        self.inactive_user = self.create_user(
            username="inactive@example.com",
            is_active=False
        )

    def test_get(self):
        report = make(Report, created_by=self.inactive_user, point=ORIGIN)
        session = self.client.session
        session['report_ids'] = [report.pk]
        session.save()
        comment = make(Comment, report=report, created_by=self.inactive_user)
        response = self.client.get(reverse("comments-edit", args=[comment.pk]))
        self.assertEqual(response.status_code, 200)

    def test_anonymous_users_are_forced_to_login(self):
        comment = make(Comment, report=make(Report, point=ORIGIN))
        response = self.client.get(reverse("comments-edit", args=[comment.pk]))
        self.assertEqual(response.status_code, 302)

    def test_not_allowed_to_edit(self):
        report = make(Report, point=ORIGIN)
        comment = make(Comment, report=report)
        self.client.login(email=self.user.email, password="foo")
        response = self.client.get(reverse("comments-edit", args=[comment.pk]))
        self.assertEqual(response.status_code, 403)

    def test_post(self):
        report = make(Report, created_by=self.inactive_user, point=ORIGIN)
        session = self.client.session
        session['report_ids'] = [report.pk]
        session.save()
        comment = make(Comment, report=report, created_by=self.inactive_user)
        data = {
            "body": "hello",
            "form-TOTAL_FORMS": "0",
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
        }
        response = self.client.post(reverse("comments-edit", args=[comment.pk]), data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Comment.objects.get(pk=comment.pk).body, "hello")

    def test_post_with_image(self):
        # make a report for a user who is allowed to login and control
        # visibility (this would be a site admin)
        report = make(Report, created_by=self.admin, point=ORIGIN)
        self.client.login(email=self.admin.email, password="admin")

        comment = make(Comment, report=report, created_by=self.admin)
        data = {
            "body": "hello",
            "visibility": Comment.PUBLIC,
            "form-TOTAL_FORMS": "1",
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            "form-0-image_data_uri": "data:image/gif;base64,R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
            "form-0-name": "Hello world",
            "form-0-visibility": Image.PUBLIC,
        }
        response = self.client.post(reverse("comments-edit", args=[comment.pk]), data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Comment.objects.get(pk=comment.pk).body, "hello")
        self.assertEqual(Image.objects.filter(comment=comment, visibility=Image.PUBLIC).count(), 1)


class CommentDeleteViewTest(TestCase, UserMixin):

    def setUp(self):
        self.user = self.create_user(
            username="foo@example.com",
            password="foo",
            is_active=True,
            is_staff=False
        )
        self.admin = self.create_user(
            username="admin@example.com",
            password="admin",
            is_active=True,
            is_staff=True
        )
        self.inactive_user = self.create_user(
            username="inactive@example.com",
            is_active=False
        )

    def test_get(self):
        report = make(Report, point=ORIGIN)
        comment = make(Comment, report=report, created_by=self.user)
        self.client.login(email=self.user.email, password="foo")
        response = self.client.get(reverse("comments-delete", args=[comment.pk]))
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        report = make(Report, point=ORIGIN)
        comment = make(Comment, report=report, created_by=self.user)
        self.client.login(email=self.user.email, password="foo")
        response = self.client.post(reverse("comments-delete", args=[comment.pk]))
        self.assertEqual(response.status_code, 302)

    def test_not_allowed_to_delete(self):
        report = make(Report, created_by=self.user, point=ORIGIN)
        comment = make(Comment, report=report)
        self.client.login(email=self.user.email, password="foo")
        response = self.client.post(reverse("comments-delete", args=[comment.pk]))
        self.assertRedirects(response, reverse("reports-detail", args=[report.pk]))


class CommentUrlizeViewTest(TestCase, UserMixin):

    def setUp(self):
        self.user = self.create_user(
            username="foo@example.com",
            password="foo",
            is_active=True
        )

    def test_get(self):
        report = make(Report, created_by=self.user, point=ORIGIN)
        comment = make(Comment, report=report, created_by=self.user, body="www.google.com")
        self.client.login(email=self.user.email, password="foo")
        self.assertEqual(Comment.objects.get(pk=comment.pk).body, "www.google.com")
        response = self.client.get(reverse("reports-detail", args=[report.pk]))
        self.assertIn('<a href="http://www.google.com"', str(response.content))


class CommentNoUrlizeViewTest(TestCase, UserMixin):

    def setUp(self):
        self.user = self.create_user(
            username="foo@example.com",
            password="foo",
            is_active=False
        )

    def test_get(self):
        report = make(Report, created_by=self.user, point=ORIGIN)
        comment = make(Comment, report=report, created_by=self.user, body="www.google.com")
        session = self.client.session
        session['report_ids'] = [report.pk]
        session.save()
        self.client.login(email=self.user.email, password="foo")
        self.assertEqual(Comment.objects.get(pk=comment.pk).body, "www.google.com")
        response = self.client.get(reverse("reports-detail", args=[report.pk]))
        self.assertContains(response, 'www.google.com')
        self.assertNotIn('<a href="http://www.google.com"', str(response.content))
