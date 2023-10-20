from django.db.models import OuterRef, Subquery, F, Case, Value, When, Exists, BooleanField, DateField, CharField, IntegerField, JSONField, FloatField
from django.contrib.gis.db import models
from localflavor.us.us_states import US_STATES

from racial_covenants_processor.storage_backends import PublicMediaStorage
from apps.plat.models import Plat, Subdivision


class CovenantsParcelManager(models.Manager):
    '''This is the main heavy-lifter for exports -- as much work as possible being done here to tag the parcel with the earliest mention of the covenant and its related attributes'''

    def get_queryset(self):
        from apps.zoon.models import ZooniverseSubject, ManualCovenant

        # annotate with deed page lookups?

        oldest_deed = ZooniverseSubject.objects.filter(
            parcel_matches=OuterRef('pk'),
            bool_covenant_final=True,
            workflow=OuterRef('workflow')
        ).only(
            'workflow',
            'zoon_subject_id',
            'image_ids',
            'image_links',
            'subject_1st_page__s3_lookup',
            'subject_2nd_page__s3_lookup',
            'subject_3rd_page__s3_lookup',
            'dt_retired',
            'bool_covenant_final',
            'covenant_text_final',
            'addition_final',
            'lot_final',
            'block_final',
            'seller_final',
            'buyer_final',
            'deed_date_final',
            'match_type_final',
            'bool_handwritten_final',
            'median_score',
            'bool_manual_correction',
            'bool_parcel_match',
            'join_candidates',
            'date_updated',
        ).order_by('deed_date_final')[:1]

        oldest_deed_manual = ManualCovenant.objects.filter(
            parcel_matches=OuterRef('pk'),
            bool_confirmed=True,
            workflow=OuterRef('workflow')
        ).order_by('deed_date')[:1]

        return super().get_queryset().defer(
            'orig_data',
        ).filter(
            bool_covenant=True
        ).annotate(
            cov_type=Case(
                When(
                    Exists(oldest_deed),
                    then=Value("zooniverse")
                ),
                When(
                    Exists(oldest_deed_manual),
                    then=Value("manual")
                ),
                default=Value(""),
                output_field=CharField()
            )
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
            deed_date=Case(
                When(
                    Exists(oldest_deed),
                    then=Subquery(oldest_deed.values('deed_date_final'))
                ),
                When(
                    Exists(oldest_deed_manual),
                    then=Subquery(oldest_deed_manual.values('deed_date'))
                ),
                default=Value(None),
                output_field=DateField()
            )
        ).annotate(
            cov_text=Case(
                When(
                    Exists(oldest_deed),
                    then=Subquery(oldest_deed.values('covenant_text_final'))
                ),
                When(
                    Exists(oldest_deed_manual),
                    then=Subquery(oldest_deed_manual.values('covenant_text'))
                ),
                default=Value(''),
                output_field=CharField()
            )
        ).annotate(
            zn_subj_id=Case(
                When(
                    Exists(oldest_deed),
                    then=Subquery(oldest_deed.values('zoon_subject_id'))
                ),
                default=Value(None),
                output_field=IntegerField()
            )
        ).annotate(
            image_ids=Case(
                When(
                    Exists(oldest_deed),
                    then=Subquery(oldest_deed.values('image_ids'))
                ),
                default=Value("[]"),
                output_field=JSONField()
            )
        ).annotate(
            image_links=Case(
                When(
                    Exists(oldest_deed),
                    then=Subquery(oldest_deed.values('image_links'))
                ),
                default=Value("[]"),
                output_field=JSONField()
            )
        ).annotate(
            deed_page_1=Case(
                When(
                    Exists(oldest_deed),
                    then=Subquery(oldest_deed.values('subject_1st_page__s3_lookup'))
                ),
                default=Value(''),
                output_field=CharField()
            )
        ).annotate(
            deed_page_2=Case(
                When(
                    Exists(oldest_deed),
                    then=Subquery(oldest_deed.values('subject_2nd_page__s3_lookup'))
                ),
                default=Value(''),
                output_field=CharField()
            )
        ).annotate(
            deed_page_3=Case(
                When(
                    Exists(oldest_deed),
                    then=Subquery(oldest_deed.values('subject_3rd_page__s3_lookup'))
                ),
                default=Value(''),
                output_field=CharField()
            )
        ).annotate(
            zn_dt_ret=Case(
                When(
                    Exists(oldest_deed),
                    then=Subquery(oldest_deed.values('dt_retired'))
                ),
                default=Value(None),
                output_field=DateField()
            )
        ).annotate(
            med_score=Case(
                When(
                    Exists(oldest_deed),
                    then=Subquery(oldest_deed.values('median_score'))
                ),
                default=Value(None),
                output_field=FloatField()
            )
        ).annotate(
            manual_cx=Case(
                When(
                    Exists(oldest_deed),
                    then=Subquery(oldest_deed.values('bool_manual_correction'))
                ),
                When(
                    Exists(oldest_deed_manual),
                    then=Value(True)
                ),
                default=Value(False),
                output_field=BooleanField()
            )
        ).annotate(
            add_cov=Case(
                When(
                    Exists(oldest_deed),
                    then=Subquery(oldest_deed.values('addition_final'))
                ),
                When(
                    Exists(oldest_deed_manual),
                    then=Subquery(oldest_deed_manual.values('addition'))
                ),
                default=Value(''),
                output_field=CharField()
            )
        ).annotate(
            block_cov=Case(
                When(
                    Exists(oldest_deed),
                    then=Subquery(oldest_deed.values('block_final'))
                ),
                When(
                    Exists(oldest_deed_manual),
                    then=Subquery(oldest_deed_manual.values('block'))
                ),
                default=Value(''),
                output_field=CharField()
            )
        ).annotate(
            lot_cov=Case(
                When(
                    Exists(oldest_deed),
                    then=Subquery(oldest_deed.values('lot_final'))
                ),
                When(
                    Exists(oldest_deed_manual),
                    then=Subquery(oldest_deed_manual.values('lot'))
                ),
                default=Value(''),
                output_field=CharField()
            )
        ).annotate(
            seller=Case(
                When(
                    Exists(oldest_deed),
                    then=Subquery(oldest_deed.values('seller_final'))
                ),
                When(
                    Exists(oldest_deed_manual),
                    then=Subquery(oldest_deed_manual.values('seller'))
                ),
                default=Value(''),
                output_field=CharField()
            )
        ).annotate(
            buyer=Case(
                When(
                    Exists(oldest_deed),
                    then=Subquery(oldest_deed.values('buyer_final'))
                ),
                When(
                    Exists(oldest_deed_manual),
                    then=Subquery(oldest_deed_manual.values('buyer'))
                ),
                default=Value(''),
                output_field=CharField()
            )
        ).annotate(
            match_type=Case(
                When(
                    Exists(oldest_deed),
                    then=Subquery(oldest_deed.values('match_type_final'))
                ),
                When(
                    Exists(oldest_deed_manual),
                    then=Subquery(oldest_deed_manual.values('cov_type'))
                ),
                default=Value(''),
                output_field=CharField()
            )
        ).annotate(
            dt_updated=Case(
                When(
                    Exists(oldest_deed),
                    then=Subquery(oldest_deed.values('date_updated'))
                ),
                When(
                    Exists(oldest_deed_manual),
                    then=Subquery(oldest_deed_manual.values('date_updated'))
                ),
                default=Value(None),
                output_field=DateField()
            )
        ).annotate(
            join_candidates=Case(
                When(
                    Exists(oldest_deed),
                    then=Subquery(oldest_deed.values('join_candidates'))
                ),
                When(
                    Exists(oldest_deed_manual),
                    then=Subquery(oldest_deed_manual.values('join_candidates'))
                ),
                default=Value("[]"),
                output_field=JSONField()
            )
        ).annotate(
            doc_num=Case(
                When(
                    Exists(oldest_deed),
                    then=Subquery(oldest_deed.values('deedpage_doc_num'))
                ),
                When(
                    Exists(oldest_deed_manual),
                    then=Subquery(oldest_deed_manual.values('doc_num'))
                ),
                default=Value(''),
                output_field=CharField()
            )
        )


class Parcel(models.Model):
    workflow = models.ForeignKey(
         "zoon.ZooniverseWorkflow", null=True, on_delete=models.SET_NULL)
    feature_id = models.IntegerField()
    pin_primary = models.CharField(max_length=50, null=True, blank=True)
    pin_secondary = models.CharField(max_length=50, null=True, blank=True)
    street_address = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(db_index=True, max_length=100, null=True, blank=True)
    state = models.CharField(db_index=True, max_length=2, null=True,
                             blank=True, choices=US_STATES)
    zip_code = models.CharField(max_length=20, null=True, blank=True)
    county_name = models.CharField(max_length=50, null=True, blank=True)
    county_fips = models.CharField(max_length=5, null=True, blank=True)
    plat_name = models.CharField(db_index=True, max_length=255, null=True, blank=True)
    plat_standardized = models.CharField(db_index=True, max_length=255, null=True, blank=True)
    block = models.CharField(max_length=255, null=True, blank=True)
    lot = models.CharField(max_length=500, null=True, blank=True)
    join_description = models.TextField(null=True, blank=True)
    phys_description = models.TextField(null=True, blank=True)
    township = models.IntegerField(null=True, blank=True)
    range = models.IntegerField(null=True, blank=True)
    section = models.IntegerField(null=True, blank=True)
    orig_data = models.JSONField(null=True, blank=True)
    orig_filename = models.CharField(max_length=255, null=True, blank=True)
    geom_4326 = models.MultiPolygonField(srid=4326)

    # Plat refers to a plat map, which is often old, and Subdivision refers to a modern GIS layer
    plat = models.ForeignKey(Plat, on_delete=models.SET_NULL, null=True)
    subdivision_spatial = models.ForeignKey(Subdivision, on_delete=models.SET_NULL, null=True)
    # zoon_subjects = models.ManyToManyField("zoon.ZooniverseSubject")

    # Hard-coded for easier filtering, set by match_parcels.py and individual save routines.
    bool_covenant = models.BooleanField(default=False, db_index=True)

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
        max_length=500, db_index=True, null=True)
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

    class Meta:
        ordering = ('-id',)


class CSVExport(models.Model):
    workflow = models.ForeignKey(
         "zoon.ZooniverseWorkflow", null=True, on_delete=models.SET_NULL)
    csv = models.FileField(
        storage=PublicMediaStorage(), upload_to="main_exports/", null=True)
    covenant_count = models.IntegerField()
    created_at = models.DateTimeField()

    class Meta:
        ordering = ('-id',)


class UnmappedCSVExport(models.Model):
    workflow = models.ForeignKey(
         "zoon.ZooniverseWorkflow", null=True, on_delete=models.SET_NULL)
    csv = models.FileField(
        storage=PublicMediaStorage(), upload_to="main_exports/", null=True)
    covenant_count = models.IntegerField()
    created_at = models.DateTimeField()

    class Meta:
        ordering = ('-id',)


class ValidationCSVExport(models.Model):
    workflow = models.ForeignKey(
         "zoon.ZooniverseWorkflow", null=True, on_delete=models.SET_NULL)
    csv = models.FileField(
        storage=PublicMediaStorage(), upload_to="main_exports/", null=True)
    covenant_count = models.IntegerField()
    created_at = models.DateTimeField()

    class Meta:
        ordering = ('-id',)


class GeoJSONExport(models.Model):
    workflow = models.ForeignKey(
         "zoon.ZooniverseWorkflow", null=True, on_delete=models.SET_NULL)
    geojson = models.FileField(
        storage=PublicMediaStorage(), upload_to="main_exports/", null=True)
    covenant_count = models.IntegerField()
    created_at = models.DateTimeField()

    class Meta:
        ordering = ('-id',)
