import datetime

from haystack.query import SearchQuerySet

from popolo import models
from popolo_name_resolver.resolve import (
    delete_entities, recreate_entities, ResolvePopoloName
)
from popolo_name_resolver.models import EntityName

from unittest import TestCase


class ExcludePeopleWithNoMiddleNames(object):

    def is_person_allowed(self, person):
        name_parts = person.name.split()
        return len(name_parts) > 2


class ResolvePopitNameTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super(ResolvePopitNameTest, cls).setUpClass()
        # Create some Popolo people:
        cls.john_q = models.Person.objects.create(
            name='John Quentin Smith',
        )
        models.Person.objects.create(
            name='John Smith',
        )
        cls.pele = models.Person.objects.create(
            name='Pele',
        )
        cls.mandela = models.Person.objects.create(
            name='Nelson Mandela',
            given_name='Nelson',
        )
        org_anc = models.Organization.objects.create(
            name='African National Congress (ANC)',
            classification='Party',
        )
        models.Membership.objects.create(
            organization=org_anc,
            person=cls.mandela,
        )
        # And create lots of EntityName objects for looking them up.
        recreate_entities(verbose=False)

    @classmethod
    def tearDownClass(cls):
        delete_entities()
        models.Person.objects.all().delete()

    def test_aaa(self):
        self.assertTrue(True) # dummy pass, to prevent annoying stacktrace of SQL DDL if first test fails

    def test_resolve(self):

        resolver = ResolvePopoloName(
                date = datetime.date(month=11, year=2010, day=1) )

        popolo_person = resolver.get_person('J Q Smith')
        self.assertEqual(self.john_q, popolo_person)

    def test_resolve_with_filter(self):
        resolver = ResolvePopoloName(
            date=datetime.date(month=11, year=2010, day=1),
            person_filter=ExcludePeopleWithNoMiddleNames(),
        )

        popolo_person = resolver.get_person('John Smith')
        self.assertEqual(popolo_person.name, 'John Quentin Smith')

    def test_org_appending(self):
        sqs = SearchQuerySet().filter(
            person=self.mandela.id
        ).models(EntityName)
        indexed_names = set(s.text for s in sqs)
        self.assertEqual(
            indexed_names,
            {
                'N Mandela (ANC)',
                'Nelson Mandela',
                'N Mandela',
                'N Mandela (African National Congress)',
                'Nelson Mandela (African National Congress)',
                'Nelson Mandela (ANC)',
            }
        )
