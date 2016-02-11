from django.core.management.base import BaseCommand

from popolo_name_resolver.resolve import recreate_entities


class Command(BaseCommand):

    def handle(self, *args, **options):
        recreate_entities()
