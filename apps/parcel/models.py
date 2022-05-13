from django.contrib.gis.db import models
from localflavor.us.us_states import US_STATES

from racial_covenants_processor.storage_backends import PublicMediaStorage
from apps.plat.models import Plat


class Parcel(models.Model):
    workflow = models.ForeignKey(
         "zoon.ZooniverseWorkflow", null=True, on_delete=models.SET_NULL)
    feature_id = models.IntegerField()
    pin_primary = models.CharField(max_length=50, null=True, blank=True)
    pin_secondary = models.CharField(max_length=50, null=True, blank=True)
    street_address = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    state = models.CharField(max_length=2, null=True,
                             blank=True, choices=US_STATES)
    zip_code = models.CharField(max_length=20, null=True, blank=True)
    county_name = models.CharField(max_length=50, null=True, blank=True)
    county_fips = models.CharField(max_length=5, null=True, blank=True)
    plat_name = models.CharField(max_length=255, null=True, blank=True)
    plat_standardized = models.CharField(max_length=255, null=True, blank=True)
    block = models.CharField(max_length=100, null=True, blank=True)
    lot = models.CharField(max_length=100, null=True, blank=True)
    join_description = models.TextField(null=True, blank=True)
    phys_description = models.TextField(null=True, blank=True)
    township = models.IntegerField(null=True, blank=True)
    range = models.IntegerField(null=True, blank=True)
    section = models.IntegerField(null=True, blank=True)
    orig_data = models.JSONField(null=True, blank=True)
    orig_filename = models.CharField(max_length=255, null=True, blank=True)
    geom_4326 = models.MultiPolygonField(srid=4326)

    plat = models.ForeignKey(Plat, on_delete=models.SET_NULL, null=True)

    @property
    def join_strings(self):
        strings = []
        for candidate in self.parceljoincandidate_set.all():
            strings.append(candidate.join_string)
        return strings


class ParcelJoinCandidate(models.Model):
    '''A given parcel can be made up of more than one lot, theoretically. This
    creates and easily queryable lookup that can be used efficiently when
    joinable records are updated'''
    workflow = models.ForeignKey(
         "zoon.ZooniverseWorkflow", null=True, on_delete=models.SET_NULL)
    parcel = models.ForeignKey(Parcel, on_delete=models.CASCADE)
    plat_name_standardized = models.CharField(
        max_length=255, db_index=True, null=True)
    join_string = models.CharField(
        max_length=255, db_index=True, null=True)
    metadata = models.JSONField(null=True, blank=True)


class JoinReport(models.Model):
    workflow = models.ForeignKey(
         "zoon.ZooniverseWorkflow", null=True, on_delete=models.SET_NULL)
    report_csv = models.FileField(
        storage=PublicMediaStorage(), upload_to="analysis/", null=True)
    covenant_count = models.IntegerField()
    matched_lot_count = models.IntegerField()
    matched_subject_count = models.IntegerField()
    created_at = models.DateTimeField()


class ShpExport(models.Model):
    workflow = models.ForeignKey(
         "zoon.ZooniverseWorkflow", null=True, on_delete=models.SET_NULL)
    shp_zip = models.FileField(
        storage=PublicMediaStorage(), upload_to="main_exports/", null=True)
    covenant_count = models.IntegerField()
    created_at = models.DateTimeField()
