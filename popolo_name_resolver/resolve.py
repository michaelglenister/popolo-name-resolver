from datetime import datetime, date
import logging
import sys
import re

from popolo.models import Person
from popolo_name_resolver.models import EntityName

from haystack.query import SearchQuerySet

logger = logging.getLogger(__name__)

# TODO these should be added to another table from honorific_prefix in SetupEntities
name_stopwords = re.compile(
    '^(Adv|Chief|Dr|Miss|Mme|Mna|Mnr|Mnu|Moh|Moruti|Moulana|Mr|Mrs|Ms|Njing|Nkk|Nksz|Nom|P|Prince|Prof|Rev|Rre|Umntwana) ')

class ResolvePopoloName (object):

    def __init__(self,
            date = None,
            date_string = None,
            person_filter = None):

        if date_string:
            date = datetime.strptime(date_string, '%Y-%m-%d')
        if not date:
            raise Exception("You must provide a date")

        self.date = date
        self.person_cache = {}
        self.person_filter = person_filter

    def get_person(self, name, party=None):

        person = self.person_cache.get((name, party), None)
        if person:
            return person

        def _get_person(name):
            if not name:
                return None

            results = ( SearchQuerySet()
                .filter(
                    content=name,
                    start_date__lte=self.date,
                    end_date__gte=self.date
                    )
                .models(EntityName)
                )

            # ElasticSearch may treat the date closeness as more important than the presence of
            # words like Deputy (oops) so we do an additional filter here
            if not re.search('Deputy', name):
                results = [r for r in results if not re.search('Deputy', r.object.name)]

            if len(results):
                for result in results:
                    person = result.object.person
                    if (self.person_filter is None or
                        self.person_filter.is_person_allowed(person)):
                        return person

        # This should ensure that we only try name variants until one
        # actually returns something:
        lazily_resolved_names = (
            _get_person(n) for n in self._get_name_variants(name, party)
        )
        person = next((p for p in lazily_resolved_names if p), None)
        if person:
            self.person_cache[(name, party)] = person
            return person
        return None

    def _get_name_variants(self, name, party):
        (name_sans_paren, paren) = self._get_name_and_paren(name)
        names_to_try = [paren] # favour this, as it might override
        if party:
            names_to_try.append(name + " " + party)
        return names_to_try + [
            name,
            name_sans_paren,
            self._strip_honorific(name),
            self._strip_honorific(name_sans_paren),
        ]

    def _strip_honorific(self, name):
        if not name:
            return None
        (stripped, changed) = re.subn( name_stopwords, '', name )
        if changed:
            return stripped
        return None

    def _get_name_and_paren(self, name):
        s = re.match(r'((?:\w|\s)+) \(((?:\w|\s)+)\)', name)
        if s:
            (pname, paren) = s.groups()
            if len(paren.split()) >= 3:
                # if parens with at least three words
                return (pname, paren)
            else:
                return (pname, None)
        return (None, None)

def get_party_name_variants(full_name):
    """Get plausible variants of a party name from its full name

    Sometimes party names have a standard abbreviation for the party
    included in brackets like: 'Economic Freedom Fighters (EFF)'.  In
    such cases this will return a sequence with possible ways of
    referring to the organization, e.g.

    >>> get_party_name_variants('Economic Freedom Fighters (EFF)')
    ('Economic Freedom Fighters', 'EFF')
    >>> get_party_name_variants('Conservative Party')
    ('Conservative Party',)
    """
    m = re.search(r'^\s*(.*?)\s*\((.*)\)$', full_name)
    if m:
        return m.groups()
    else:
        return (full_name,)

def _get_possible_initials(person):

    result = set()

    given_names = person.given_name.split()
    first_names = person.name.split()[:-1]

    for names in (given_names, first_names):
        if not names:
            continue
        # Extracts all of those names, and try versions where they're
        # separated by spaces and right next to each
        # other. (e.g. John Happy becomes "J H" and "JH")
        initials = [a[:1] for a in names]
        result.add(' '.join(initials))
        result.add(''.join(initials))
        # Also try just the initial of the first name:
        result.add(names[0][:1])
        # In South Africa, sometimes the way people are recorded
        # is using only their second initial, so try that as well.
        # FIXME: maybe this should be scored lower than other variants...
        if len(initials) >= 2:
            result.add(initials[1])

    return result

def _get_family_name(person):

    if person.family_name:
        return person.family_name

    given_name = person.given_name
    if given_name and person.name.startswith(given_name):
        family_name = person.name.replace(given_name, '', 1).strip()
        return family_name

    return person.name.rsplit(' ', 1)[1]

def _dates(membership):
    def get_date(field):
        value = getattr(membership, field)
        if not value:
            return None
        # FIXME this is wrong for end_dates, where we should look at
        # the day before the next month / year:
        value = value.replace('-00', '-01')
        try:
            return datetime.strptime(value, '%Y-%m-%d')
        except:
            return None
    return [
        get_date('start_date'),
        get_date('end_date'),
        ]

def delete_entities():
    EntityName.objects.all().delete()

def recreate_entities(verbose=False):
    # Remove all EntityName objects from the database (and search
    # index):
    delete_entities()

    total_people = Person.objects.count()
    done = 0

    for person in Person.objects.all():
        name = person.name
        if not name:
            continue

        def make_name(**kwargs):
            kwargs['person'] = person
            kwargs['start_date'] = kwargs.get('start_date') or date(year=2000, month=1, day=1)
            kwargs['end_date'] = kwargs.get('end_date') or date(year=2030, month=1, day=1)
            return EntityName.objects.get_or_create(**kwargs)

        possible_initials = _get_possible_initials(person)
        family_name = _get_family_name(person)
        honorifics = set([person.honorific_prefix, ''])

        def concat_name(names):
            return ' '.join(n for n in names if n)

        possible_names = set()

        for honorific in honorifics:
            full_name = concat_name( [honorific, name] )
            possible_names.add(full_name)
            for initials in possible_initials:
                name_with_initials = concat_name( [honorific, initials, family_name] )
                possible_names.add(name_with_initials)

        for possible_name in possible_names:
            make_name(name=possible_name)

        # Now this script also creates names which include the
        # organization name too:

        for membership in person.memberships.all():
            if not membership.organization:
                continue
            organization = membership.organization
            organization_names = set([organization.name])
            for other_name in organization.other_names.all():
                organization_names.add(other_name.name)
            start_date, end_date = _dates(membership)

            classification = organization.classification.lower()

            if classification == 'party':
                for n in possible_names:
                    for organization_name in organization_names:
                        for p in get_party_name_variants(organization['name']):
                            name_with_party = '%s (%s)' % (n, p)
                            make_name(
                                name=name_with_party,
                                start_date=start_date,
                                end_date=end_date)

            role = membership.role
            label = membership.label

            party_mship = (classification == 'party' and role == 'Member')
            candidate_list_mship = re.search(r'^\d+.* Candidate$', role)

            if not (party_mship or candidate_list_mship):
                # FIXME: I suspect we could drop this completely
                # with very few problems, but haven't tested that.
                for membership_label in (role, label):
                    if not membership_label:
                        continue

                    make_name(
                        name=' '.join( [membership_label, organization_name] ),
                        start_date=start_date,
                        end_date=end_date)

        done += 1

        if verbose:
            message = "Done {0} out of {1} people ({2}%)"
            print message.format(done, total_people, (done * 100) / total_people)
