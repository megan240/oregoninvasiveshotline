from django.test import RequestFactory, TestCase
from django.urls import reverse
from model_bakery.baker import make

from ..models import Category, Severity, Species
from ..views import (
    CategoryCreateView,
    CategoryDeleteView,
    CategoryDetailView,
    SeverityCreateView,
    SeverityDeleteView,
    SeverityDetailView,
    SpeciesCreateView,
    SpeciesDeleteView,
    SpeciesDetailView,
)


class CategoryTest(TestCase):
    def test_str(self):
        self.assertEqual(str(make(Category, name="foo")), "foo")


class SeverityTest(TestCase):
    def test_str(self):
        self.assertEqual(str(make(Severity, name="foo")), "foo")


class SpeciesTest(TestCase):
    def test_str(self):
        self.assertEqual(str(make(Species, name="foo", scientific_name="bar")), "foo (bar)")

# View tests


class SpeciesCreateViewTest(TestCase):

    def test_get_success_url(self):

        self.factory = RequestFactory()
        request = self.factory.get(reverse("species-create"))
        view = SpeciesCreateView()
        view.request = request
        full_path = view.get_success_url()
        self.assertEqual(full_path, reverse("species-list"))


class SpeciesDetailViewTest(TestCase):

    def test_get_success_url(self):

        new_species = make(Species)
        self.factory = RequestFactory()
        request = self.factory.get(reverse("species-detail", args=[new_species.pk]))
        view = SpeciesDetailView()
        view.request = request
        full_path = view.get_success_url()
        self.assertEqual(full_path, request.get_full_path())


class SpeciesDeleteViewTest(TestCase):

    def test_get_context_data(self):

        new_species = make(Species)
        self.factory = RequestFactory()
        request = self.factory.get(reverse("species-delete", args=[new_species.pk]))
        view = SpeciesDeleteView()
        view.request = request
        view.kwargs = {'pk': new_species.pk}
        view.object = view.get_object()
        view.context = view.get_context_data()
        self.assertTrue(view.context['will_be_deleted_with'])


class CategoryCreateViewTest(TestCase):

    def test_get_success_url(self):

        self.factory = RequestFactory()
        request = self.factory.get(reverse("categories-create"))
        view = CategoryCreateView()
        view.request = request
        full_path = view.get_success_url()
        self.assertEqual(full_path, reverse("categories-list"))


class CategoryDetailViewTest(TestCase):

    def test_get_success_url(self):

        new_category = make(Category)
        self.factory = RequestFactory()
        request = self.factory.get(reverse("categories-detail", args=[new_category.pk]))
        view = CategoryDetailView()
        view.request = request
        full_path = view.get_success_url()
        self.assertEqual(full_path, reverse("categories-list"))


class CategoryDeleteViewTest(TestCase):

    def test_get_context_data(self):

        new_species = make(Species)
        self.factory = RequestFactory()
        request = self.factory.get(reverse("categories-delete", args=[new_species.category.pk]))
        view = CategoryDeleteView()
        view.request = request
        view.kwargs = {'pk': new_species.category.pk}
        view.object = view.get_object()
        view.context = view.get_context_data()
        self.assertTrue(view.context['will_be_deleted_with'])


class SeverityCreateViewTest(TestCase):

    def test_get_success_url(self):

        self.factory = RequestFactory()
        request = self.factory.get(reverse("severities-create"))
        view = SeverityCreateView()
        view.request = request
        full_path = view.get_success_url()
        self.assertEqual(full_path, reverse("severities-list"))


class SeverityDetailViewTest(TestCase):

    def test_get_success_url(self):

        new_severity = make(Severity)
        self.factory = RequestFactory()
        request = self.factory.get(reverse("severities-detail", args=[new_severity.pk]))
        view = SeverityDetailView()
        view.request = request
        full_path = view.get_success_url()
        self.assertEqual(full_path, reverse("severities-list"))


class SeverityDeleteViewTest(TestCase):

    def test_get_context_data(self):

        new_species = make(Species)
        self.factory = RequestFactory()
        request = self.factory.get(reverse("severities-delete", args=[new_species.severity.pk]))
        view = SeverityDeleteView()
        view.request = request
        view.kwargs = {'pk': new_species.severity.pk}
        view.object = view.get_object()
        view.context = view.get_context_data()
        self.assertTrue(view.context['will_be_deleted_with'])
