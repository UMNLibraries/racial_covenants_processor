from django.db.models import Prefetch
from django.db.models import OuterRef, Subquery, F
from django.contrib.gis.db import models
from localflavor.us.us_states import US_STATES

from racial_covenants_processor.storage_backends import PublicMediaStorage
from apps.plat.models import Plat


class CovenantsParcelManager(models.Manager):
    '''This is the main heavy-lifter for exports -- as much work as possible being done here to tag the parcel with the earliest mention of the covenant and its related attributes'''
    def get_queryset(self):
        from apps.zoon.models import ZooniverseSubject
        oldest_deeds = ZooniverseSubject.objects.filter(
            bool_covenant_final=True,
            parcel_matches=OuterRef('pk'),
            workflow=OuterRef('workflow')
        ).order_by('deed_date')

        return super().get_queryset().filter(
            zooniversesubject__bool_covenant_final=True
        ).annotate(
            deed_date=Subquery(oldest_deeds.values('deed_date')[:1])
        # ).annotate(
        #     all_deed_dates=F('zooniversesubject__deed_date')
        ).annotate(
            covenant_text=Subquery(oldest_deeds.values('covenant_text_final')[:1])
        ).annotate(
            zoon_subject_id=Subquery(oldest_deeds.values('zoon_subject_id')[:1])
        ).annotate(
            image_ids=Subquery(oldest_deeds.values('image_ids')[:1])
        ).annotate(
            zoon_dt_retired=Subquery(oldest_deeds.values('dt_retired')[:1])
        ).annotate(
            median_score=Subquery(oldest_deeds.values('median_score')[:1])
        ).annotate(
            manual_cx=Subquery(oldest_deeds.values('bool_manual_correction')[:1])
        ).annotate(
            addition_cov=Subquery(oldest_deeds.values('addition_final')[:1])
        ).annotate(
            lot_cov=Subquery(oldest_deeds.values('lot_final')[:1])
        ).annotate(
            block_cov=Subquery(oldest_deeds.values('block_final')[:1])
        ).annotate(
            seller=Subquery(oldest_deeds.values('seller_final')[:1])
        ).annotate(
            buyer=Subquery(oldest_deeds.values('buyer_final')[:1])
        ).annotate(
            deed_date=Subquery(oldest_deeds.values('deed_date_final')[:1])
        ).annotate(
            match_type=Subquery(oldest_deeds.values('match_type_final')[:1])
        ).annotate(
            date_updated=Subquery(oldest_deeds.values('date_updated')[:1])
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
