from django.test import TestCase
from model_bakery.baker import make

from oregoninvasiveshotline.users.models import User

from ..forms import SpeciesSearchForm
from ..models import Species


class SpeciesSearchFormTest(TestCase):

    def setUp(self):
        super().setUp()
        make(Species, name='stuff')
        self.user = User(first_name='foo', last_name='bar', email='foobar@example.com', is_staff=True)
        self.user.set_password('foobar')
        self.user.save()
        self.client.login(username='foobar@example.com', password='foobar')

    def test_get_initial_queryset(self):
        form = SpeciesSearchForm(data={'q': ''})
        results = form.search(Species.objects.all())
        self.assertEqual(
            results.count(),
            Species.objects.count()
        )

    def test_valid_form(self):
        form = SpeciesSearchForm({'q': 'other'})
        self.assertTrue(form.is_valid())

    def test_form_with_empty_querystring_returns_everything(self):
        form = SpeciesSearchForm({'q': ''})
        self.assertTrue(form.is_valid())
        results = form.search(Species.objects.all())
        self.assertEqual(
            results.count(),
            Species.objects.count()
        )

    def test_search_returns_correct_object(self):
        # test object
        name = 'dog'
        make(Species, name=name)
        # set it all up
        form = SpeciesSearchForm({'q': name})
        # make sure the form is valid
        self.assertTrue(form.is_valid())
        results = form.search(Species.objects.all())[0]
        # Check to see that the id of the test object "other"
        # is in the list of ids returned by the search function
        self.assertEqual(results.name, name)

    def test_order_by_field_sorts_species(self):
        make(Species, name='albatross', scientific_name='diomedeidae')
        make(Species, name='buffalo', scientific_name='bison')
        make(Species, name='cat', scientific_name='felis catus')

        form = SpeciesSearchForm({
            'q': '',
            'order_by': 'name',
            'order': 'descending',
        })
        species = form.search(Species.objects.all())

        self.assertTrue(species, Species.objects.all().order_by('-name'))
