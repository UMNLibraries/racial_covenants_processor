from django.db.models import OuterRef, Subquery, F
from django.contrib.gis.db import models
from localflavor.us.us_states import US_STATES

from racial_covenants_processor.storage_backends import PublicMediaStorage
from apps.plat.models import Plat


class CovenantsParcelManager(models.Manager):
    '''This is the main heavy-lifter for exports -- as much work as possible being done here to tag the parcel with the earliest mention of the covenant and its related attributes'''

    def get_queryset(self):
        from apps.zoon.models import ZooniverseSubject

        oldest_deed = ZooniverseSubject.objects.filter(
            parcel_matches=OuterRef('pk'),
            bool_covenant_final=True,
            workflow=OuterRef('workflow')
        ).order_by('deed_date')[:1]

        return super().get_queryset().filter(
            zooniversesubject__bool_covenant_final=True
        ).annotate(
            add_mod=F('plat_name')
        ).annotate(
            block_mod=F('block')
        ).annotate(
            lot_mod=F('lot')
        ).annotate(
            street_add=F('street_address')
        ).annotate(
            ph_dsc_mod=F('phys_description')
        ).annotate(
            cnty_name=F('county_name')
        ).annotate(
            cnty_fips=F('county_fips')
        ).annotate(
            cnty_pin=F('pin_primary')
        ).annotate(
            deed_date=Subquery(oldest_deed.values('deed_date'))
        ).annotate(
            cov_text=Subquery(oldest_deed.values('covenant_text_final'))
        ).annotate(
            zn_subj_id=Subquery(oldest_deed.values('zoon_subject_id'))
        ).annotate(
            image_ids=Subquery(oldest_deed.values('image_ids'))
        ).annotate(
            zn_dt_ret=Subquery(oldest_deed.values('dt_retired'))
        ).annotate(
            med_score=Subquery(oldest_deed.values('median_score'))
        ).annotate(
            manual_cx=Subquery(oldest_deed.values('bool_manual_correction'))
        ).annotate(
            add_cov=Subquery(oldest_deed.values('addition_final'))
        ).annotate(
            block_cov=Subquery(oldest_deed.values('block_final'))
        ).annotate(
            lot_cov=Subquery(oldest_deed.values('lot_final'))
        ).annotate(
            seller=Subquery(oldest_deed.values('seller_final'))
        ).annotate(
            buyer=Subquery(oldest_deed.values('buyer_final'))
        ).annotate(
            deed_date=Subquery(oldest_deed.values('deed_date_final'))
        ).annotate(
            match_type=Subquery(oldest_deed.values('match_type_final'))
        ).annotate(
            dt_updated=Subquery(oldest_deed.values('date_updated'))
        ).annotate(
            join_candidates=Subquery(oldest_deed.values('join_candidates'))
        )


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
    # zoon_subjects = models.ManyToManyField("zoon.ZooniverseSubject")

    objects = models.Manager()
    covenant_objects = CovenantsParcelManager()

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


class CSVExport(models.Model):
    workflow = models.ForeignKey(
         "zoon.ZooniverseWorkflow", null=True, on_delete=models.SET_NULL)
    csv = models.FileField(
        storage=PublicMediaStorage(), upload_to="main_exports/", null=True)
    covenant_count = models.IntegerField()
    created_at = models.DateTimeField()


class GeoJSONExport(models.Model):
    workflow = models.ForeignKey(
         "zoon.ZooniverseWorkflow", null=True, on_delete=models.SET_NULL)
    geojson = models.FileField(
        storage=PublicMediaStorage(), upload_to="main_exports/", null=True)
    covenant_count = models.IntegerField()
    created_at = models.DateTimeField()
