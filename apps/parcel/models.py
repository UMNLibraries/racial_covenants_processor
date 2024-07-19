from django.db.models import OuterRef, Subquery, F, Case, Value, When, Exists, BooleanField, DateField, CharField, IntegerField, JSONField, FloatField
from django.contrib.gis.db import models
from django.dispatch import receiver
from localflavor.us.us_states import US_STATES

from postgres_copy import CopyManager

from racial_covenants_processor.storage_backends import PublicMediaStorage
from apps.plat.models import Plat, Subdivision
from .utils.parcel_utils import get_all_parcel_options


class CovenantsParcelManager(models.Manager):
    '''This is the main heavy-lifter for exports -- as much work as possible being done here to tag the parcel with the earliest mention of the covenant and its related attributes. A lot of work gets done here. The oldest_deed line finds the oldest covenant document linked to a parcel, which determines the exported covenant date and which ZooniverseSubject will be used (in case of duplication) to populate things like the covenant text, buyer and seller. This manager also brings together covenants identified via Zooniverse transcription (ZooniverseSubject objects) and covenants entered manually (ManualCovenant.)'''

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
    '''A modern GIS parcel record imported from a shapefile, generally sourced from a county GIS system or open records portal. Imported via load_parcel_shp management command. Racial covenant exports (besides unmapped documents) are aggregated to identify the earliest recorded covenant for each modern parcel, which means each row in covenants exports is equivalent to one Parcel object. By filling out the parcel_shps -> mapping object in the workflow config, users can tell the load_parcel_shp management command which attributes/columns in the original shapefile correspond to the attribute names needed to import into the Parcel table.'''
    workflow = models.ForeignKey(
         "zoon.ZooniverseWorkflow", null=True, on_delete=models.SET_NULL)
    feature_id = models.IntegerField()
    '''A unique identifier in the original shapefile.'''
    pin_primary = models.CharField(max_length=50, null=True, blank=True)
    '''The primary property identification number used by the records custodian to look up the parcel in modern systems.'''
    pin_secondary = models.CharField(max_length=50, null=True, blank=True)
    '''An optional secondary identification number used by the records custodian to look up the parcel in modern systems.'''
    street_address = models.CharField(max_length=255, null=True, blank=True)
    '''The street address of the parcel, e.g. "123 Main Street" Note that many counties have columns for both the address of the parcel AND the address of the responsible taxpayer, so be sure that this is the address of the parcel, often known as the situs address'''
    city = models.CharField(db_index=True, max_length=100, null=True, blank=True)
    '''The city name where the parcel is located. (Not taxpayer city.)'''
    state = models.CharField(db_index=True, max_length=2, null=True,
                             blank=True, choices=US_STATES)
    '''The 2-digit state abbreviation where the parcel is located. (Not taxpayer state.)'''
    zip_code = models.CharField(max_length=20, null=True, blank=True)
    '''The zip code where the parcel is located. (Not taxpayer zip.)'''
    county_name = models.CharField(max_length=50, null=True, blank=True)
    '''The county name where the parcel is located. (Usually set statically for whole county at import)'''
    county_fips = models.CharField(max_length=5, null=True, blank=True)
    '''The 5-digit U.S. Census county FIPS where the parcel is located. (Usually set statically for whole county at import). Note that FIPS codes may change with each decenniel census.'''
    plat_name = models.CharField(db_index=True, max_length=255, null=True, blank=True)
    '''The addition name of this parcel, as it originally appears (not standardized).'''
    plat_standardized = models.CharField(db_index=True, max_length=255, null=True, blank=True)
    '''The addition name of this parcel, standardized by running plat_name through a series of regexes.'''
    block = models.CharField(max_length=255, null=True, blank=True)
    '''The block or square name of this parcel.'''
    lot = models.CharField(max_length=500, null=True, blank=True)
    '''The lot number or letter of this parcel.'''
    join_description = models.TextField(null=True, blank=True)
    '''The full physical description of this parcel. Not used for matching as yet.'''
    phys_description = models.TextField(null=True, blank=True)
    '''The full physical description of this parcel, generally a duplicate of join_description. Not well thought out.'''
    township = models.IntegerField(null=True, blank=True)
    '''In the PLSS system, the township of this parcel. Not particularly useful currently, but good information to have.'''
    range = models.IntegerField(null=True, blank=True)
    '''In the PLSS system, the range of this parcel. Not particularly useful currently, but good information to have.'''
    section = models.IntegerField(null=True, blank=True)
    '''In the PLSS system, the section of this parcel. Not particularly useful currently, but good information to have.'''
    orig_data = models.JSONField(null=True, blank=True)
    '''A JSON field storing the original set of attributes found in the shapefile under their original column names, including values not imported to a Deed Machine field. Can be accessed via Django shell.'''
    orig_filename = models.CharField(max_length=255, null=True, blank=True)
    '''The original filename of the imported shapefile.'''
    geom_4326 = models.MultiPolygonField(srid=4326)
    '''Multipolygon geometry of the parcel, in SRID:4326 coordinate reference system (WGS-84). Make sure that your shapefile has been correctly transformed to SRID:4326 if it was originally projected to another coordinate system. If you experience import errors due to invalid geometries, try using "Repair geometries" in the QGIS Processing Toolbox or equivalent tool.'''

    plat = models.ForeignKey(Plat, on_delete=models.SET_NULL, null=True)
    """Plat refers to a plat map, which is often old, and Subdivision refers to a modern GIS layer"""
    subdivision_spatial = models.ForeignKey(Subdivision, on_delete=models.SET_NULL, null=True)
    """The Subdivision object that this parcel lies inside, geospatially. May not have the same name as plat_name."""

    bool_covenant = models.BooleanField(default=False, db_index=True)
    """Has this Parcel been linked to a confirmed racial covenant? Set by match_parcels.py and individual save routines of ZooniverseSubject, ManualCovenant, PlatAlternateName, and SubdivisionAlternateName."""

    objects = models.Manager()
    """Manager used to list all Parcel rows, not just parcels linked to covenants."""
    covenant_objects = CovenantsParcelManager()
    """Manager used to list only parcels linked to racial covenants See CovenantsParcelManager() for details."""

    def __str__(self):
        return f"{self.county_name} {self.plat_name} LOT {self.lot} BLOCK {self.block} ({self.pk})"

    @property
    def join_strings(self):
        strings = []
        for candidate in self.parceljoincandidate_set.all():
            strings.append(candidate.join_string)
        return strings
    
    def save(self, *args, **kwargs):
        # Rebuild ParcelJoinCandidate objects, which will incorporate ManualParcelCandidate objects
        ParcelJoinCandidate.objects.filter(parcel=self).delete()
        candidates = get_all_parcel_options(self)
        join_cands = []
        for c in candidates:
            join_cands.append(ParcelJoinCandidate(
                workflow=self.workflow,
                parcel=self,
                plat_name_standardized=self.plat_standardized,
                join_string=c['join_string'],
                metadata=c['metadata']
            ))
        print('Candidates generated, saving to DB...')
        ParcelJoinCandidate.objects.bulk_create(join_cands, batch_size=2000)

        super(Parcel, self).save(*args, **kwargs)


class ParcelJoinCandidate(models.Model):
    '''A given parcel can be made up of more than one lot, theoretically. This
    creates and easily queryable lookup that can be used efficiently when
    joinable records are updated'''
    workflow = models.ForeignKey(
         "zoon.ZooniverseWorkflow", null=True, on_delete=models.SET_NULL)
    parcel = models.ForeignKey(Parcel, on_delete=models.CASCADE)
    """Foreign key to parcel record this is tied to"""
    plat_name_standardized = models.CharField(
        max_length=255, db_index=True, null=True)
    """Addition/plat name after filtering"""
    join_string = models.CharField(
        max_length=500, db_index=True, null=True)
    """Join string associated with this candidate, which is what will be used to attempt auto-mapping"""
    metadata = models.JSONField(null=True, blank=True)
    """Information about the filtering/processing of this candidate, see parcel_utils.py"""


class ManualParcelCandidate(models.Model):
    '''Similar to ExtraParcelCandidate on ZooniverseSubject, this would let you fill out a smart range of lots in combo with addition and block, and would generate additional join strings. To be used where the physical description is difficult to automatically parse, but simple lots are extractable manually.'''
    workflow = models.ForeignKey(
         "zoon.ZooniverseWorkflow", null=True, on_delete=models.SET_NULL)
    parcel = models.ForeignKey(Parcel, on_delete=models.CASCADE)
    """Foreign key to parcel record this is tied to"""

    parcel_pin_primary = models.CharField(max_length=50, null=True, blank=True)
    """Primary PIN number (not DB ID) of the parcel this candidate is linked to. These are kept separate of the foreign key relationship in case this needs to be reconnected later by import/export process."""

    addition = models.CharField(max_length=500, null=True, blank=True)
    """User-entered addition/plat/subdivision. Must be filled out to generate join string."""
    lot = models.TextField(null=True, blank=True)
    """User-entered lot, which can be any parseable lot value, like "1", "1-3", "1,2,3". Must be filled out to generate join string."""
    block = models.CharField(max_length=500, null=True, blank=True)
    """User-entered block. One ManualParcelCandidate should be added for each block or addition needed. May be blank."""

    date_added = models.DateTimeField(auto_now_add=True)
    """Auto-generated"""
    date_updated = models.DateTimeField(auto_now=True)
    """Auto-generated"""

    comments = models.TextField(null=True, blank=True)
    """User comments on why this ManualParcelCandidate has been added."""

    objects = CopyManager()

    def save(self, *args, **kwargs):
        """Saving a ManualParcelCandidate populates values needed for export/import, and also triggers the attached Parcel to run its save routine to re-generate its set of parcel candidates."""
        self.workflow = self.parcel.workflow
        self.parcel_pin_primary = self.parcel.pin_primary
        super(ManualParcelCandidate, self).save(*args, **kwargs)
        self.parcel.save()

@receiver(models.signals.post_delete, sender=ManualParcelCandidate)
def model_delete(sender, instance, **kwargs):
    """If ManualParcelCandidate is deleted, re-run the parent Parcel save method to remove it from the list of join candidates used by Parcel"""
    try:
        instance.parcel.save()
    except AttributeError:
        pass


class JoinReport(models.Model):
    """A CSV report generated in the course of the match_parcels management command to show what racial covenants did and didn't successfully match to a Parcel record. File saved to S3."""
    workflow = models.ForeignKey(
         "zoon.ZooniverseWorkflow", null=True, on_delete=models.SET_NULL)
    report_csv = models.FileField(
        storage=PublicMediaStorage(), upload_to="analysis/", null=True)
    covenanted_doc_count = models.IntegerField()
    matched_lot_count = models.IntegerField()
    matched_subject_count = models.IntegerField()
    created_at = models.DateTimeField()


class ShpExport(models.Model):
    """One of the Deed Machine's main public data exports. A shapefile export of modern properties that have confirmed racial covenants. Generated by dump_covenants_shp management command. File saved to S3 by default, but can be saved locally as well."""
    workflow = models.ForeignKey(
         "zoon.ZooniverseWorkflow", null=True, on_delete=models.SET_NULL)
    shp_zip = models.FileField(
        storage=PublicMediaStorage(), upload_to="main_exports/", null=True)
    covenant_count = models.IntegerField()
    created_at = models.DateTimeField()

    class Meta:
        ordering = ('-id',)


class GeoJSONExport(models.Model):
    """One of the Deed Machine's main public data exports. A GeoJSON export of modern properties that have confirmed racial covenants. Generated by dump_covenants_geojson management command. File saved to S3 by default, but can be saved locally as well."""
    workflow = models.ForeignKey(
         "zoon.ZooniverseWorkflow", null=True, on_delete=models.SET_NULL)
    geojson = models.FileField(
        storage=PublicMediaStorage(), upload_to="main_exports/", null=True)
    covenant_count = models.IntegerField()
    created_at = models.DateTimeField()

    class Meta:
        ordering = ('-id',)


class CSVExport(models.Model):
    """One of the Deed Machine's main public data exports. A CSV export of modern properties that have confirmed racial covenants. Generated by dump_covenants_csv management command. File saved to S3 by default, but can be saved locally as well."""
    workflow = models.ForeignKey(
         "zoon.ZooniverseWorkflow", null=True, on_delete=models.SET_NULL)
    csv = models.FileField(
        storage=PublicMediaStorage(), upload_to="main_exports/", null=True)
    covenant_count = models.IntegerField()
    created_at = models.DateTimeField()

    class Meta:
        ordering = ('-id',)


class UnmappedCSVExport(models.Model):
    """One of the Deed Machine's main public data exports. A CSV export of confirmed racial covenants that have not successfully been matched to a Parcel yet. Generated by dump_unmapped_csv management command. File saved to S3 by default, but can be saved locally as well."""
    workflow = models.ForeignKey(
         "zoon.ZooniverseWorkflow", null=True, on_delete=models.SET_NULL)
    csv = models.FileField(
        storage=PublicMediaStorage(), upload_to="main_exports/", null=True)
    covenant_count = models.IntegerField()
    created_at = models.DateTimeField()

    class Meta:
        ordering = ('-id',)


class ValidationCSVExport(models.Model):
    """I don't remember what this is for."""
    workflow = models.ForeignKey(
         "zoon.ZooniverseWorkflow", null=True, on_delete=models.SET_NULL)
    csv = models.FileField(
        storage=PublicMediaStorage(), upload_to="main_exports/", null=True)
    covenant_count = models.IntegerField()
    created_at = models.DateTimeField()

    class Meta:
        ordering = ('-id',)


class AllCovenantedDocsCSVExport(models.Model):
    """A CSV export of all documents that have confirmed racial covenants, whether they have been mapped or not. Note that the count of these rows will differ from the main Deed Machine exports because this is a list of all documents, not all parcels with covenants. (Racial covenants on a propery are often repeated in subsequent sales.) This export is useful for determining which documents may need to be flagged in property records for racial language. Generated by dump_all_covenanted_docs management command. File saved to S3 by default, but can be saved locally as well."""
    workflow = models.ForeignKey(
         "zoon.ZooniverseWorkflow", null=True, on_delete=models.SET_NULL)
    csv = models.FileField(
        storage=PublicMediaStorage(), upload_to="main_exports/", null=True)
    doc_count = models.IntegerField()
    created_at = models.DateTimeField()

    class Meta:
        ordering = ('-id',)
