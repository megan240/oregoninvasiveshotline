from unittest.mock import Mock

from django.core import mail
from django.contrib.gis.geos import Point
from django.test import TestCase
from django.urls import reverse

from model_bakery.baker import make

from oregoninvasiveshotline.utils.test.user import UserMixin
from oregoninvasiveshotline.reports.models import Report
from oregoninvasiveshotline.species.models import Category

from .models import UserNotificationQuery


ORIGIN = Point(0, 0)


class CreateViewTest(TestCase, UserMixin):

    def setUp(self):
        self.user = self.create_user(
            username='foo@example.com',
            password='foo',
            is_active=True,
            is_staff=False
        )

    def test_only_active_users_can_view_page(self):
        self.client.login(email=self.user.email, password='foo')
        self.user.is_active = False
        self.user.save()
        response = self.client.get(reverse('notifications-create'))
        self.assertEqual(response.status_code, 403)

    def test_get(self):
        self.client.login(email=self.user.email, password='foo')
        response = self.client.get(reverse('notifications-create'))
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        self.client.login(email=self.user.email, password='foo')
        pre_count = UserNotificationQuery.objects.count()
        response = self.client.post(reverse('notifications-create') + '?q=foo', {
            'name': 'bar'
        })
        self.assertRedirects(response, reverse('reports-list') + '?q=foo')
        self.assertEqual(UserNotificationQuery.objects.count(), pre_count+1)


class ListViewTest(TestCase, UserMixin):

    def test_get(self):
        user = self.create_user(username='foo@example.com', password='foo', is_active=True)
        make(UserNotificationQuery, user=user, query='?q=foo')
        self.client.login(email=user.email, password='foo')
        response = self.client.get(reverse('notifications-list'))
        self.assertEqual(response.status_code, 200)


class UserNotificationQueryPrettyQuery(TestCase, UserMixin):

    def test_pretty_query(self):
        user = self.create_user(username='foo@example.com')
        category1 = Category.objects.create(name='Ocean Animal')
        category2 = Category.objects.create(name='Pencil')
        subscription = UserNotificationQuery.objects.create(
            query='q=foobarius&categories={0}&categories={1}'.format(category1.pk, category2.pk),
            user=user,
        )
        expected_output = {
            'Categories': 'Ocean Animal, Pencil',
            'Keyword': 'foobarius'
        }
        self.assertEqual(subscription.pretty_query, expected_output)
