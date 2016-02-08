from django.db import models

from popolo.models import Person

class EntityName(models.Model):
    name = models.TextField(db_index=True)
    start_date = models.DateField(blank=True, null=True, help_text='What date did this name/position start')
    end_date   = models.DateField(blank=True, null=True, help_text='What date did this name/position end')
    person     = models.ForeignKey(
        Person, 
        on_delete=models.PROTECT, 
        help_text='The Popolo Person that this is a possible name for')
