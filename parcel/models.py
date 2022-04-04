from django.contrib.gis.db import models

from localflavor.us.us_states import US_STATES
from zoon.models import ZooniverseWorkflow


class Parcel(models.Model):
    workflow = models.ForeignKey(ZooniverseWorkflow, null=True, on_delete=models.SET_NULL)
    pin_primary = models.CharField(max_length=50, blank=True)
    pin_secondary = models.CharField(max_length=50, blank=True)
    street_address = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=2, blank=True, choices=US_STATES)
    zip_code = models.CharField(max_length=20, blank=True)
    county_name = models.CharField(max_length=50, blank=True)
    county_fips = models.CharField(max_length=5, blank=True)
    plat_name = models.CharField(max_length=255, blank=True)
    block = models.CharField(max_length=100, blank=True)
    lot = models.CharField(max_length=100, blank=True)
    join_description = models.CharField(max_length=100, blank=True)
    phys_description = models.TextField(blank=True)
    township = models.IntegerField(null=True, blank=True)
    range = models.IntegerField(null=True, blank=True)
    section = models.IntegerField(null=True, blank=True)
    orig_data = models.JSONField(null=True, blank=True)
    geom = models.MultiPolygonField(srid=4326)
