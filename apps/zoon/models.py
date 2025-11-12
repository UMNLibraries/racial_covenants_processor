import json
from django.contrib.gis.db import models
from django.contrib.gis.db.models.aggregates import Union
from django.contrib.gis import geos
from django.db.models import F, Value, Count, OuterRef, Case, When, Exists, Subquery, CharField

# from django.db.models import OuterRef, Subquery, F, Case, Value, When, Exists, BooleanField, DateField, CharField, IntegerField, JSONField, FloatField
from django.dispatch import receiver
from django.utils.text import slugify

from postgres_copy import CopyManager

from racial_covenants_processor.storage_backends import PublicMediaStorage
from apps.plat.models import Plat, PlatAlternateName, Subdivision, SubdivisionAlternateName
from apps.parcel.models import Parcel
from apps.parcel.utils.parcel_utils import build_parcel_spatial_lookups, gather_all_covenant_candidates, gather_all_manual_covenant_candidates, standardize_addition, addition_wide_parcel_match
from apps.zoon.utils.zooniverse_join import set_addresses


class ZooniverseWorkflow(models.Model):
    '''The main shell that keeps each project separate from others. Generally, each county will require a separate ZooniverseWorkflow object.'''
    zoon_id = models.IntegerField(null=True, blank=True, db_index=True)
    workflow_name = models.CharField(max_length=100, db_index=True)
    # version = models.FloatField(null=True, blank=True)
    version = models.CharField(max_length=20, null=True, blank=True)
    slug = models.CharField(max_length=100, db_index=True, blank=True)

    def __str__(self):
        return self.workflow_name
    
    def save(self, *args, **kwargs):
        self.slug = self.get_slug()
        super(ZooniverseWorkflow, self).save(*args, **kwargs)

    def get_slug(self):
        return slugify(self.workflow_name)


MATCH_TYPE_OPTIONS = (
    ('SL', 'Simple lot'),
    ('ML', 'Multiple single lots'),
    ('MB', 'Lots spanning multiple blocks'),
    ('PL', 'Partial lot'),
    ('PD', 'Long phys description'),
    ('AW', 'Addition-wide covenant'),
    ('C', 'Cemetery plot'),
    ('PC', 'Petition covenant'),
    ('SE', 'Something else'),
    ('NG', 'No geographic information'),
)


class UnmappedZooniverseManager(models.Manager):
    '''This model manager is mainly used for exports OF NON-MAPPED COVENANTS ONLY. The main model manager used for covenant exports is in apps/parcel/models.py. Unlike the main exporter, de-duping is not done here to eliminate multiple occurences of the same document, and is not currently possible for unmapped covenants.'''

    def get_queryset(self):

        return super().get_queryset().filter(
            bool_covenant_final=True,
            bool_parcel_match=False
        ).annotate(
            # deed_date=F('deed_date_final'),  # Need to rename with pd
            cov_text=F('covenant_text_final'),
            zn_subj_id=F('zoon_subject_id'),
            zn_dt_ret=F('dt_retired'),
            med_score=F('median_score'),
            manual_cx=F('bool_manual_correction'),
            add_cov=F('addition_final'),
            block_cov=F('block_final'),
            lot_cov=F('lot_final'),
            # map_book=F('map_book_final'),
            # map_page=F('map_book_page_final'),
            city_cov=F('city_final'),
            # seller=F('seller_final'),  # Need to rename with pd
            # buyer=F('buyer_final'),  # Need to rename with pd
            dt_updated=F('date_updated'),
            doc_num=F('deedpage_doc_num'),
            cov_type=Value('zooniverse'),
            # match_type=Value('unmapped')  # Need to rename with pd
        )


class AllCovenantedDocsZooniverseManager(models.Manager):
    '''This model manager is mainly used for exports of all covenanted documents.
    It returns a list of all covenant/parcel combinations, so should not be used for covenant counts.
    It is reduced to a per-docnumber list in the export stage in apps/parcel/utils/export_utils.py
    The main model manager used for covenant exports is in apps/parcel/models.py.
    Unlike the main exporter, de-duping is not done here to eliminate multiple occurences
    of the same document.'''
    

    def get_queryset(self):
        from apps.deed.models import DeedPage

        deed_page = DeedPage.objects.filter(
            s3_lookup=OuterRef('deedpage_s3_lookup'),
            workflow=OuterRef('workflow')
        ).only(
            'page_image_web_highlighted'
        )

        return super().get_queryset().filter(
            bool_covenant_final=True
        ).annotate(
            db_id=F('pk'),
            # deed_date=F('deed_date_final'),  # Need to rename with pd
            is_mapped=F('bool_parcel_match'),
            cov_text=F('covenant_text_final'),
            zn_subj_id=F('zoon_subject_id'),
            zn_dt_ret=F('dt_retired'),
            med_score=F('median_score'),
            manual_cx=F('bool_manual_correction'),
            add_cov=F('addition_final'),
            block_cov=F('block_final'),
            lot_cov=F('lot_final'),
            # map_book=F('map_book_final'),  # Need to rename with pd
            # map_page=F('map_book_page_final'),  # Need to rename with pd
            join_strgs=F('join_candidates'),
            # city_cov=F('city_final'),
            # seller=F('seller_final'),  # Need to rename with pd
            # buyer=F('buyer_final'),  # Need to rename with pd
            dt_updated=F('date_updated'),
            doc_num=F('deedpage_doc_num'),
            cov_type=Value('zooniverse'),
            # match_type=Value('unmapped')  # Need to rename with pd
            # addresses=F('parcel_addresses'),
            mapped_address=F('parcel_matches__street_address'),
            mapped_city=F('parcel_matches__city'),
            mapped_state=F('parcel_matches__state'),
            mapped_parcel_pin=F('parcel_matches__pin_primary'),
            main_image=F('deedpage_s3_lookup'),
            # highlight_image=F('page_image_web_highlighted')
        ).annotate(
            highlight_image=Case(
                When(
                    Exists(deed_page),
                    then=Subquery(deed_page.values('page_image_web_highlighted'))
                ),
                default=Value(''),
                output_field=CharField()
            ),
            web_image=Case(
                When(
                    Exists(deed_page),
                    then=Subquery(deed_page.values('page_image_web'))
                ),
                default=Value(''),
                output_field=CharField()
            )
        )


class ValidationZooniverseManager(models.Manager):
    '''This model manager is used to run statistics on retired subjects and
    for other analysis purposes'''

    def get_queryset(self):

        # TODO: Add response count
#         from django.db.models import Count
# comments = Comments.objects.annotate(num_answers=Count('answers'))

        return super().get_queryset().annotate(
            # deed_date=F('deed_date_final'),  # Need to rename with pd
            cov_text=F('covenant_text_final'),
            zn_subj_id=F('zoon_subject_id'),
            zn_dt_ret=F('dt_retired'),
            resp_count=Count('responses'),
            med_score=F('median_score'),
            cov_score=F('bool_covenant_score'),
            hand_score=F('bool_handwritten_score'),
            mtype_score=F('match_type_score'),
            text_score=F('covenant_text_score'),
            add_score=F('addition_score'),
            # lot_score=F('lot_score'),
            # block_score=F('block_score'),
            # city_score=F('city_score'),
            sell_score=F('seller_score'),
            buy_score=F('buyer_score'),
            manual_cx=F('bool_manual_correction'),
            add_cov=F('addition_final'),
            block_cov=F('block_final'),
            lot_cov=F('lot_final'),
            map_book=F('map_book_final'),
            map_page=F('map_book_page_final'),
            city_cov=F('city_final'),
            # seller=F('seller_final'),  # Need to rename with pd
            # buyer=F('buyer_final'),  # Need to rename with pd
            dt_updated=F('date_updated'),
            doc_num=F('deedpage_doc_num'),
            cov_type=Value('zooniverse'),
            # match_type=Value('unmapped')  # Need to rename with pd
        )


# class CopyJSONField(models.JSONField):
#     '''How to translate imported JSON from CSV to avoid import errors. See https://palewi.re/docs/django-postgres-copy/#import-options'''
#     # copy_template = """
#     #     REPLACE(REPLACE ("%(name)s", '''', '"'), 'None', 'null')::json
#     # """


class ZooniverseSubject(models.Model):
    '''This is the main model representing an individual suspected covenant coming back from Zooniverse transcription. Each subject should have five individual transcription responses, which will be aggregated to be displayed with each ZooniverseSubject. Possible future task: Assign an id to correspond to a deed image pre-Zooniverse'''
    workflow = models.ForeignKey(ZooniverseWorkflow, on_delete=models.CASCADE)
    zoon_subject_id = models.IntegerField(db_index=True)

    image_ids = models.JSONField(blank=True)  # used to be links, future will be s3_lookup, might be unnecessary?
    image_links = models.JSONField(blank=True, null=True)

    dt_retired = models.DateTimeField(null=True)

    # This part comes from the reducers
    bool_covenant = models.BooleanField(null=True)
    bool_problem = models.BooleanField(default=False)
    covenant_text = models.TextField(blank=True)
    addition = models.CharField(max_length=501, blank=True)
    lot = models.TextField(blank=True)
    block = models.CharField(max_length=502, blank=True)

    map_book = models.CharField(max_length=255, null=True, blank=True)
    map_book_page = models.CharField(max_length=255, null=True, blank=True)

    city = models.CharField(max_length=503, blank=True)
    seller = models.CharField(max_length=1200, blank=True)
    buyer = models.CharField(max_length=1200, blank=True)
    deed_date = models.DateField(null=True)

    # Match type not a part of Ramsey County workflow but will be used in future.
    match_type = models.CharField(choices=MATCH_TYPE_OPTIONS, max_length=4, null=True, blank=True)
    bool_handwritten = models.BooleanField(null=True)

    # Data used to join back to deedpage
    deedpage_pk = models.IntegerField(null=True, blank=True)
    deedpage_doc_num = models.CharField(max_length=50, null=True, blank=True)
    deedpage_s3_lookup = models.CharField(max_length=255, null=True, blank=True)

    # Scores, also from the reducers
    bool_covenant_score = models.FloatField(null=True)
    bool_handwritten_score = models.FloatField(null=True)
    match_type_score = models.FloatField(null=True)
    covenant_text_score = models.FloatField(null=True)
    addition_score = models.FloatField(null=True)
    lot_score = models.FloatField(null=True)
    block_score = models.FloatField(null=True)
    map_book_score = models.FloatField(null=True)
    map_book_page_score = models.FloatField(null=True)
    city_score = models.FloatField(null=True)
    seller_score = models.FloatField(null=True)
    buyer_score = models.FloatField(null=True)

    deed_date_overall_score = models.FloatField(null=True)
    deed_date_year_score = models.FloatField(null=True)
    deed_date_month_score = models.FloatField(null=True)
    deed_date_day_score = models.FloatField(null=True)

    median_score = models.FloatField(null=True)

    # Final values created by combining zooniverse entry with any manual corrections separately entered. Only written under the hood, not directly in the admin, so if we have to delete/re-import, manual work stored in the manual update won't be lost
    bool_manual_correction = models.BooleanField(
        null=True, default=False, verbose_name="Manual updates?")

    bool_covenant_final = models.BooleanField(
        null=True, verbose_name="Racial covenant?")
    covenant_text_final = models.TextField(
        null=True, blank=True, verbose_name="Covenant text")
    addition_final = models.CharField(
        max_length=500, null=True, blank=True, verbose_name="Addition")
    lot_final = models.TextField(null=True, blank=True, verbose_name="Lot")
    block_final = models.CharField(
        max_length=500, null=True, blank=True, verbose_name="Block")
    map_book_final = models.CharField(
        max_length=255, null=True, blank=True, verbose_name="Map Book")
    map_book_page_final = models.CharField(
        max_length=255, null=True, blank=True, verbose_name="Map Book Page")
    seller_final = models.CharField(
        max_length=1200, null=True, blank=True, verbose_name="Seller name")
    buyer_final = models.CharField(
        max_length=1200, null=True, blank=True, verbose_name="Buyer name")
    deed_date_final = models.DateField(
        null=True, blank=True, verbose_name="Deed date")

    street_address_final = models.TextField(null=True, blank=True, verbose_name="Street address")
    city_final = models.CharField(
        max_length=500, null=True, blank=True, verbose_name="City")
    match_type_final = models.CharField(choices=MATCH_TYPE_OPTIONS, max_length=4, null=True, blank=True, verbose_name="Match type")
    bool_handwritten_final = models.BooleanField(null=True, verbose_name="Handwritten?")

    parcel_matches = models.ManyToManyField('parcel.Parcel')
    # parcel_manual = models.ManyToManyField(ManualParcel)  # TODO
    bool_parcel_match = models.BooleanField(default=False, verbose_name="Parcel match?")


    join_candidates = models.JSONField(null=True, blank=True)

    # Fields resulting from join to Parcel models
    parcel_addresses = models.JSONField(null=True, blank=True)
    parcel_city = models.CharField(max_length=50, null=True, blank=True, db_index=True)

    # Union of any joined parcels
    geom_union_4326 = models.MultiPolygonField(
        srid=4326, null=True, blank=True)

    date_updated = models.DateTimeField(auto_now=True, null=True)

    # objects = models.Manager()
    objects = CopyManager()
    unmapped_objects = UnmappedZooniverseManager()
    all_covenanted_docs_objects = AllCovenantedDocsZooniverseManager()
    validation_objects = ValidationZooniverseManager()

    def __str__(self):
        return f"{self.workflow} {self.zoon_subject_id}"

    # def copy_image_ids_template(self):
    #     return """
    #     to_jsonb(REPLACE ("%(name)s", '''', '"'))
    #     """

    @property
    def deed_pages(self):
        dps = []
        try:
            dps.append(self.subject_1st_page.all()[0])
        except:
            pass
        try:
            dps.append(self.subject_2nd_page.all()[0])
        except:
            pass
        try:
            dps.append(self.subject_3rd_page.all()[0])
        except:
            pass
        return dps

    @property
    def join_strings(self):
        if self.join_candidates:
            return "; ".join([c['join_string'] for c in self.join_candidates])
        return None

    def get_geom_union(self):
        union = self.parcel_matches.all().aggregate(union=Union('geom_4326'))
        if 'union' in union and union['union'] is not None:
            union_final = union['union'].unary_union
            # Force to multipolygon
            if union_final and isinstance(union_final, geos.Polygon):
                union_final = geos.MultiPolygon(union_final)
            return union_final
        return None

    # def get_parcel_addresses(self):
    #     return list(self.parcel_matches.all().values('street_address', 'city', 'state', 'zip_code'))

    # def get_parcel_cities(self):
    #     return self.parcel_matches.all().values_list('city', flat=True)

    # def set_addresses(self):
    #     if self.bool_parcel_match:
    #         self.parcel_addresses = json.dumps(self.get_parcel_addresses())
    #         cities = self.get_parcel_cities()
    #         if len(cities) > 0:
    #             # Assuming for the most part that we can generally take the first city we find. There will be edge cases, but those can be accessed via the address JSON object and this one is more of a shorthand
    #             self.parcel_city = cities[0]

    def set_geom_union(self):
        if self.bool_parcel_match:
            self.geom_union_4326 = self.get_geom_union()
        else:
            self.geom_union_4326 = None

    def check_bool_manual_update(self):
        if self.manualcorrection_set.count() > 0 or self.extraparcelcandidate_set.count() > 0 or self.manualparcelpinlink_set.count() > 0:
            self.bool_manual_correction = True
        else:
            self.bool_manual_correction = False

    def get_final_value(self, attr, blank_value=""):
        if self.manualcorrection_set.count() > 0:
            if getattr(self.manualcorrection_set.first(), attr) not in [None, blank_value]:
                return getattr(self.manualcorrection_set.first(), attr)
        return getattr(self, attr)

    def get_from_parcel_or_cx(self, attr, blank_value=""):
        # In cases where city is coming from Zooniverse, it's unlikely that
        # parcel linking will be a factor. So skip parcel matching step.
        # Currently, this only affects legacy content from Essex County, Mass.
        if attr == 'city' and self.city != '':
            if getattr(self.manualcorrection_set.first(), 'city') not in [None, blank_value]:
                return getattr(self.manualcorrection_set.first(), 'city')
            return self.city

        # ManualCorrection trumps value set automatically by linked parcel
        if self.manualcorrection_set.count() > 0:
            if getattr(self.manualcorrection_set.first(), attr) not in [None, blank_value]:
                return getattr(self.manualcorrection_set.first(), attr)
        # Otherwise, use parcel value if present
        if self.bool_parcel_match:
            output = []
            for pm in self.parcel_matches.all():
                value = getattr(pm, attr)
                if value not in [None, blank_value]:
                    output.append(getattr(pm, attr))
            return '; '.join(sorted(set(output)))
        return None

    def get_final_values(self):
        self.check_bool_manual_update()
        self.bool_covenant_final = self.get_final_value('bool_covenant')
        self.covenant_text_final = self.get_final_value('covenant_text')
        self.addition_final = self.get_final_value('addition')
        self.lot_final = self.get_final_value('lot')
        self.block_final = self.get_final_value('block')
        self.map_book_final = self.get_final_value('map_book')
        self.map_book_page_final = self.get_final_value('map_book_page')
        self.seller_final = self.get_final_value('seller')
        self.buyer_final = self.get_final_value('buyer')
        self.match_type_final = self.get_final_value('match_type')
        self.bool_handwritten_final = self.get_final_value('bool_handwritten')
        self.deed_date_final = self.get_final_value('deed_date', None)

        self.street_address_final = self.get_from_parcel_or_cx(
            'street_address')
        self.city_final = self.get_from_parcel_or_cx('city')

    def check_parcel_match(self, parcel_lookup=None):
        # Look for parcels linked only to this one, and clear bool_covenant for those
        solo_parcels = self.parcel_matches.annotate(
            num_linked_subjects=Count('zooniversesubject'),
            num_man_covs=Count('manualcovenant')
        ).filter(num_linked_subjects=1, num_man_covs=0)
        if solo_parcels.count() > 0:
            solo_parcels.update(bool_covenant=False)

        # Clear existing parcel matches
        self.parcel_matches.clear()
        self.bool_parcel_match = False

        join_strings = []
        # Main parcel
        # Save hasn't been committed yet, so need to use get_final_value
        if self.get_final_value('bool_covenant') is True:
            if self.match_type_final == 'AW':
                addition_wide_parcel_match(self)
            elif self.addition_final != '' and self.lot_final != '':
                if not parcel_lookup:
                    parcel_lookup = build_parcel_spatial_lookups(self.workflow)
                self.join_candidates = gather_all_covenant_candidates(self)
                # print(self.join_candidates)

                for c in self.join_candidates:
                    join_strings.append(c['join_string'])
                    try:
                        lot_match = parcel_lookup[c['join_string']]
                        print(f"MATCH: {c['join_string']}")

                        # There can be more than one modern parcel with same lot designation -- weird!
                        for parcel_id in lot_match['parcel_ids']:
                            self.parcel_matches.add(parcel_id)
                        # self.parcel_matches.add(lot_match['parcel_id'])
                        self.bool_parcel_match = True
                    except:
                        print(f"NO MATCH: {c['join_string']}")

            # Parcel PIN matches
            mppl_pins = ManualParcelPINLink.objects.filter(zooniverse_subject=self).values_list('parcel_pin', flat=True)
            if len(mppl_pins) > 0:
                parcel_pin_matches = Parcel.objects.filter(workflow=self.workflow, pin_primary__in=mppl_pins).values_list('pk', flat=True)
                if len(parcel_pin_matches) > 0:
                    self.bool_parcel_match = True
                for parcel_id in parcel_pin_matches:
                    self.parcel_matches.add(parcel_id)

            # Tag matched parcels with bool_covenant=True
            self.parcel_matches.all().update(bool_covenant=True)

    def save(self, *args, **kwargs):
        if self.pk:
            self.get_final_values()
            
            # Can pass parcel lookup for bulk matches
            self.check_parcel_match(kwargs.get('parcel_lookup', None))
            if 'parcel_lookup' in kwargs:
                del kwargs['parcel_lookup']

            self.set_geom_union()
            set_addresses(self)

        super(ZooniverseSubject, self).save(*args, **kwargs)

        # Generate flattened covenants for easier export. This has to run post-save or else the values for ZooniverseSubject will not get propogated to the Parcel.covenant_objects call that is needed to generate the flat CovenantedParcel record.
        if self.parcel_matches.count() > 0:
            from apps.parcel.utils.export_utils import save_flat_covenanted_parcels, delete_flat_covenanted_parcels
            delete_flat_covenanted_parcels(self.parcel_matches)
            save_flat_covenanted_parcels(self.parcel_matches)


class ZooniverseResponseRaw(models.Model):
    '''Information imported after Zooniverse transcription in its natural state after Zooniverse's panoptes-aggregation scripts. Most useful data is still contained inside annotations and subject_data fields, which will be further processed to produce a ZooniverseResponseProcessed.'''
    classification_id = models.IntegerField()
    user_name = models.CharField(max_length=100, blank=True, db_index=True)
    user_id = models.IntegerField(null=True)
    # user_ip = models.CharField(max_length=10, blank=True)  # Removed from import in order to reduce personal info stored in database
    workflow_id = models.IntegerField(null=True)
    workflow_name = models.CharField(max_length=100, blank=True)
    workflow_version = models.FloatField()
    created_at = models.DateTimeField()
    gold_standard = models.BooleanField(null=True)
    expert = models.BooleanField(null=True)
    metadata = models.JSONField()
    annotations = models.JSONField()
    subject_data = models.JSONField()
    subject_ids = models.IntegerField(db_index=True)
    subject_data_flat = models.JSONField(null=True)

    # Joined after subjects loaded
    subject = models.ForeignKey(
        ZooniverseSubject, null=True, on_delete=models.SET_NULL)

    objects = CopyManager()


class ZooniverseResponseProcessed(models.Model):
    '''Information about an individual transcription that will show up under a ZooniverseSubject during manual review. A more fully processed version of ZooniverseResponseRaw.'''
    workflow = models.ForeignKey(ZooniverseWorkflow, on_delete=models.CASCADE)
    classification_id = models.IntegerField()
    user_name = models.CharField(max_length=100, blank=True, db_index=True)
    user_id = models.IntegerField(null=True, db_index=True)
    subject = models.ForeignKey(
        ZooniverseSubject, null=True, on_delete=models.SET_NULL, related_name='responses')
    
    zoon_subject_id = models.IntegerField(db_index=True, null=True, blank=True) # Needed only for migration to another workflow

    bool_covenant = models.CharField(max_length=100, null=True, blank=True)
    covenant_text = models.TextField(blank=True)
    addition = models.CharField(max_length=500, null=True, blank=True)
    lot = models.TextField(null=True, blank=True)
    block = models.CharField(max_length=500, null=True, blank=True)
    map_book = models.CharField(max_length=255, null=True, blank=True)
    map_book_page = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=500, null=True, blank=True)  # When addition/block/lot not available in workflow
    seller = models.CharField(max_length=1200, null=True, blank=True)
    buyer = models.CharField(max_length=1200, null=True, blank=True)
    match_type = models.CharField(max_length=100, null=True, blank=True)
    bool_handwritten = models.CharField(max_length=50, null=True, blank=True)
    deed_date_year = models.CharField(max_length=10, blank=True)
    deed_date_month = models.CharField(max_length=100, blank=True)
    deed_date_day = models.CharField(max_length=10, blank=True)
    created_at = models.DateTimeField()
    response_raw = models.ForeignKey(
        ZooniverseResponseRaw, on_delete=models.CASCADE, null=True)
    
    objects = CopyManager()


class ZooniverseUser(models.Model):
    '''Temp: duplicated from apps.deed.models. May or may not be needed later, but not actually doing anything on this app currently.'''
    zoon_id = models.IntegerField(null=True, db_index=True)
    zoon_name = models.CharField(max_length=100, blank=True, db_index=True)


QUESTION_TYPE_CHOICES = (
    ('q', 'question'),
    ('d', 'dropdown')
)


class ReducedResponse_Question(models.Model):
    '''Used for both question and dropdown types'''
    zoon_subject_id = models.IntegerField(db_index=True)
    zoon_workflow_id = models.IntegerField(db_index=True)
    # TODO: add batch or date
    task_id = models.CharField(db_index=True, max_length=4)
    question_type = models.CharField(
        max_length=1, db_index=True, choices=QUESTION_TYPE_CHOICES)
    best_answer = models.TextField()
    best_answer_score = models.FloatField()
    total_votes = models.IntegerField()
    answer_scores = models.JSONField()


class ReducedResponse_Text(models.Model):
    zoon_subject_id = models.IntegerField(db_index=True)
    zoon_workflow_id = models.IntegerField(db_index=True)
    # TODO: add batch or date
    task_id = models.CharField(db_index=True, max_length=4)
    aligned_text = models.JSONField()
    total_votes = models.IntegerField()
    consensus_text = models.TextField()
    consensus_score = models.IntegerField()
    user_ids = models.JSONField()

    # TODO: Need to get individual "something is wrong" responses direct from classifier, since reduce won't handle these well. Or use a different reducer that doesn't, um, reduce


class ManualCorrection(models.Model):
    '''This is set up as a separate model to preserve any manual work that is done in the event a re-import of zooniverse data is needed'''
    workflow = models.ForeignKey(
        ZooniverseWorkflow, on_delete=models.SET_NULL, null=True)
    zooniverse_subject = models.ForeignKey(
        ZooniverseSubject, on_delete=models.SET_NULL, null=True)

    # These are kept separate of the foreign key relationship in case this needs to be reconnected later
    zoon_subject_id = models.IntegerField(db_index=True, null=True, blank=True)
    zoon_workflow_id = models.IntegerField(
        db_index=True, null=True, blank=True)

    bool_covenant = models.BooleanField(null=True)
    covenant_text = models.TextField(null=True, blank=True)
    addition = models.CharField(max_length=500, null=True, blank=True)
    lot = models.TextField(null=True, blank=True)
    block = models.CharField(max_length=500, null=True, blank=True)
    map_book = models.CharField(max_length=255, null=True, blank=True)
    map_book_page = models.CharField(max_length=255, null=True, blank=True)
    seller = models.CharField(max_length=500, null=True, blank=True)
    buyer = models.CharField(max_length=500, null=True, blank=True)
    deed_date = models.DateField(null=True, blank=True)

    street_address = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)

    date_added = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    match_type = models.CharField(choices=MATCH_TYPE_OPTIONS, max_length=4, null=True, blank=True)
    bool_handwritten = models.BooleanField(null=True)
    comments = models.TextField(null=True, blank=True)

    objects = CopyManager()

    def save(self, *args, **kwargs):
        self.workflow = self.zooniverse_subject.workflow
        self.zoon_workflow_id = self.zooniverse_subject.workflow.zoon_id
        self.zoon_subject_id = self.zooniverse_subject.zoon_subject_id
        super(ManualCorrection, self).save(*args, **kwargs)

        # self.zooniverse_subject.get_final_values()
        self.zooniverse_subject.save()


EPC_TYPE_CHOICES = (
    ('el', 'Extra deed lot (old)'),
    ('me', 'Modern equivalent lot'),
)


class ExtraParcelCandidate(models.Model):
    '''For use when property spans more than one block or addition, NOT for multiple lots in same addition/block for the moment'''
    workflow = models.ForeignKey(
        ZooniverseWorkflow, on_delete=models.SET_NULL, null=True)
    zooniverse_subject = models.ForeignKey(
        ZooniverseSubject, on_delete=models.SET_NULL, null=True)

    epc_type = models.CharField(max_length=2, choices=EPC_TYPE_CHOICES, blank=True, null=True)

    # These are kept separate of the foreign key relationship in case this needs to be reconnected later
    zoon_subject_id = models.IntegerField(db_index=True, null=True, blank=True)
    zoon_workflow_id = models.IntegerField(
        db_index=True, null=True, blank=True)

    addition = models.CharField(max_length=500, null=True, blank=True)
    lot = models.TextField(null=True, blank=True)
    block = models.CharField(max_length=500, null=True, blank=True)

    date_added = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    comments = models.TextField(null=True, blank=True)

    objects = CopyManager()

    def save(self, *args, **kwargs):
        self.workflow = self.zooniverse_subject.workflow
        self.zoon_workflow_id = self.zooniverse_subject.workflow.zoon_id
        self.zoon_subject_id = self.zooniverse_subject.zoon_subject_id
        super(ExtraParcelCandidate, self).save(*args, **kwargs)
        self.zooniverse_subject.save()  # Does this really need to trigger every time? Seems so, but causes problems on large numbers of EPCs


class ManualParcelPINLink(models.Model):
    '''A way to link to a parcel not based on join strings -- a direct link to a manually entered modern Parcel PIN that matches a Parcel object'''
    workflow = models.ForeignKey(
        ZooniverseWorkflow, on_delete=models.SET_NULL, null=True)
    zooniverse_subject = models.ForeignKey(
        ZooniverseSubject, on_delete=models.SET_NULL, null=True)

    # These are kept separate of the foreign key relationship in case this needs to be reconnected later
    zoon_subject_id = models.IntegerField(db_index=True, null=True, blank=True)
    zoon_workflow_id = models.IntegerField(
        db_index=True, null=True, blank=True)

    parcel_pin = models.CharField(max_length=50, null=True, blank=True, db_index=True)

    date_added = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    comments = models.TextField(null=True, blank=True)

    objects = CopyManager()

    def save(self, *args, **kwargs):
        self.workflow = self.zooniverse_subject.workflow
        self.zoon_workflow_id = self.zooniverse_subject.workflow.zoon_id
        self.zoon_subject_id = self.zooniverse_subject.zoon_subject_id
        super(ManualParcelPINLink, self).save(*args, **kwargs)
        self.zooniverse_subject.save()  # Does this really need to trigger every time? Seems so.


@receiver(models.signals.post_delete, sender=ManualCorrection)
def model_delete(sender, instance, **kwargs):
    try:
        instance.zooniverse_subject.get_final_values()
        instance.zooniverse_subject.save()
    except AttributeError:
        pass


@receiver(models.signals.post_delete, sender=ExtraParcelCandidate)
def model_delete(sender, instance, **kwargs):
    try:
        instance.zooniverse_subject.get_final_values()
        instance.zooniverse_subject.save()
    except AttributeError:
        pass


@receiver(models.signals.post_delete, sender=ManualParcelPINLink)
def model_delete(sender, instance, **kwargs):
    try:
        instance.zooniverse_subject.get_final_values()
        instance.zooniverse_subject.save()
    except AttributeError:
        pass



class AllCovenantedDocsManualCovenantManager(models.Manager):
    '''This model manager is mainly used for exports of all covenanted documents.
    It returns a list of all covenant/parcel combinations, so should not be used for covenant counts.
    It is reduced to a per-docnumber list in the export stage in apps/parcel/utils/export_utils.py
    The main model manager used for covenant exports is in apps/parcel/models.py.
    Unlike the main exporter, de-duping is not done here to eliminate multiple occurences
    of the same document.'''

    def get_queryset(self):

        return super().get_queryset().filter(
            # bool_covenant=True  # They all are covenants
            bool_confirmed=True
        ).annotate(
            db_id=F('pk'),
            # deed_date=F('deed_date_final'),  # Need to rename with pd
            is_mapped=F('bool_parcel_match'),
            cov_text=F('covenant_text'),
            zn_subj_id=Value(''),
            zn_dt_ret=Value(''),
            med_score=Value(''),
            manual_cx=Value(''),
            add_cov=F('addition'),
            block_cov=F('block'),
            lot_cov=F('lot'),
            # map_book=F('map_book'),
            # map_page=F('map_page'),
            join_strgs=F('join_candidates'),
            dt_updated=F('date_updated'),
            # cov_type_manual=Value('manual'),
            mapped_address=F('parcel_matches__street_address'),
            mapped_city=F('parcel_matches__city'),
            mapped_state=F('parcel_matches__state'),
            mapped_parcel_pin=F('parcel_matches__pin_primary'),
        )


MANUAL_COV_OPTIONS = (
    ('PS', 'Public submission (single property)'),
    ('SE', 'Something else'),
    ('PT', 'Plat covenant'),
)


class ManualCovenant(models.Model):
    workflow = models.ForeignKey(
        ZooniverseWorkflow, on_delete=models.CASCADE, null=True)
    bool_confirmed = models.BooleanField(default=False)
    covenant_text = models.TextField(blank=True)
    addition = models.CharField(max_length=500, blank=True)
    lot = models.TextField(null=True, blank=True)
    block = models.CharField(max_length=500, null=True, blank=True)
    map_book = models.CharField(max_length=255, null=True, blank=True)
    map_book_page = models.CharField(max_length=255, null=True, blank=True)
    seller = models.CharField(max_length=500, blank=True)
    buyer = models.CharField(max_length=500, blank=True)
    deed_date = models.DateField(null=True, blank=True)
    doc_num = models.CharField(blank=True, max_length=100, db_index=True)

    city = models.CharField(max_length=500, null=True, blank=True, verbose_name="City")

    cov_type = models.CharField(choices=MANUAL_COV_OPTIONS, max_length=4, null=True, blank=True)
    comments = models.TextField(null=True, blank=True)

    join_candidates = models.JSONField(null=True, blank=True)
    parcel_matches = models.ManyToManyField('parcel.Parcel')
    bool_parcel_match = models.BooleanField(default=False, verbose_name="Parcel match?")

    date_added = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    # Fields resulting from join to Parcel models
    parcel_addresses = models.JSONField(null=True, blank=True)
    parcel_city = models.CharField(max_length=50, null=True, blank=True, db_index=True)

    # objects = models.Manager()
    objects = CopyManager()
    all_covenanted_docs_objects = AllCovenantedDocsManualCovenantManager()

    # TODO: manual geometries

    def __str__(self):
        return f"{self.workflow} {self.addition} {self.block} {self.lot}"

    @property
    def join_strings(self):
        if self.join_candidates:
            return "; ".join([c['join_string'] for c in self.join_candidates])
        return None

    def check_parcel_match(self, parcel_lookup=None):
        ''' Triggered by post_save signal'''

        # Look for parcels linked only to this one, and clear bool_covenant for those
        solo_parcels = self.parcel_matches.annotate(
            num_linked_subjects=Count('zooniversesubject'),
            num_man_covs=Count('manualcovenant')
        ).filter(num_linked_subjects=1, num_man_covs=0)
        if solo_parcels.count() > 0:
            solo_parcels.update(bool_covenant=False)

        self.parcel_matches.clear()
        self.bool_parcel_match = False
        self.join_candidates = ''
        join_strings = []

        # For plat covenant, separate routine to find all with matching addition
        if self.bool_confirmed:
            if self.cov_type == 'PT':
                addition_wide_parcel_match(self)

            # TODO: filter by parcel other? Or just make someone add plat or plat alternate. If so, need way to manually add plat
            # Method for one-off covenants that is more similar to previous joinstring setup
            elif self.lot != '':
                if not parcel_lookup:
                    parcel_lookup = build_parcel_spatial_lookups(self.workflow)
                self.join_candidates = gather_all_manual_covenant_candidates(self)
                print(self.join_candidates)

                for c in self.join_candidates:
                    join_strings.append(c['join_string'])
                    try:
                        lot_match = parcel_lookup[c['join_string']]
                        print(f"MATCH: {c['join_string']}")

                        # There can be more than one modern parcel with same lot designation -- weird!
                        for parcel_id in lot_match['parcel_ids']:
                            self.parcel_matches.add(parcel_id)
                        # self.parcel_matches.add(lot_match['parcel_id'])
                        self.bool_parcel_match = True
                    except:
                        print(f"NO MATCH: {c['join_string']}")
            
            # Parcel PIN matches
            mppl_pins = ManualCovenantParcelPINLink.objects.filter(manual_covenant=self).values_list('parcel_pin', flat=True)
            if len(mppl_pins) > 0:
                parcel_pin_matches = Parcel.objects.filter(workflow=self.workflow, pin_primary__in=mppl_pins).values_list('pk', flat=True)
                if len(parcel_pin_matches) > 0:
                    self.bool_parcel_match = True
                for parcel_id in parcel_pin_matches:
                    self.parcel_matches.add(parcel_id)

            # Tag matched parcels with bool_covenant=True
            self.parcel_matches.all().update(bool_covenant=True)

            # Generate flattened covenants for easier export. Trying to run this as part of parcel_match process because on ManualCovenant this is sent by post-save signal, in contrast to ZooniverseSubject
            if self.parcel_matches.count() > 0:
                from apps.parcel.utils.export_utils import save_flat_covenanted_parcels, delete_flat_covenanted_parcels
                delete_flat_covenanted_parcels(self.parcel_matches)
                save_flat_covenanted_parcels(self.parcel_matches)

    def save(self, *args, **kwargs):
        
        super(ManualCovenant, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Custom logic before deletion to keep CovenantedParcels up to date
        parcel_match_pks = list(self.parcel_matches.values_list('pk', flat=True))

        # Call the parent class's delete method
        super().delete(*args, **kwargs)

        if len(parcel_match_pks) > 0:
            print('found some matches to clear')
            from apps.parcel.utils.export_utils import save_flat_covenanted_parcels, delete_flat_covenanted_parcels
            parcels_to_clear = Parcel.objects.filter(pk__in=parcel_match_pks).only('id')
            delete_flat_covenanted_parcels(parcels_to_clear)
            save_flat_covenanted_parcels(parcels_to_clear)


@receiver(models.signals.post_save, sender=ManualCovenant)
def manual_cov_post_save(sender, instance=None, created=False, **kwargs):

    if not instance:
        return

    if hasattr(instance, '_dirty'):
        return
    
    # # Can pass parcel lookup for bulk matches
    # instance.check_parcel_match(kwargs.get('parcel_lookup', None))
    # Can pass parcel lookup for bulk matches
    print('Checking parcel matches')
    instance.check_parcel_match(kwargs.get('parcel_lookup', None))
    if 'parcel_lookup' in kwargs:
        del kwargs['parcel_lookup']

    try:
        set_addresses(instance)
        instance._dirty = True
        instance.save()
    finally:
        del instance._dirty


# @receiver(models.signals.post_delete, sender=ManualCovenant)
# def cleanup_covenanted_parcels(sender, instance, **kwargs):
#     """
#     This function is called before an instance of ManualCovenant is deleted.
#     It can be used to perform cleanup or related actions.
#     """
#     print(f"Post-delete signal triggered for ManualCovenant instance: {instance.id}")

#     # Example: Delete related objects that are not handled by on_delete cascade
#     # or perform other cleanup tasks.
#     # For instance, if you have a 'RelatedModel' that should be deleted
#     # when 'MyModel' is deleted, but it's not a direct ForeignKey with CASCADE.

#     if instance.parcel_matches.count() > 0:
#         print('found some matches')
#         from apps.parcel.utils.export_utils import save_flat_covenanted_parcels, delete_flat_covenanted_parcels
#         delete_flat_covenanted_parcels(instance.parcel_matches)
#         save_flat_covenanted_parcels(instance.parcel_matches)


class ManualCovenantParcelPINLink(models.Model):
    '''A way to link to a parcel not based on join strings -- a direct link to a manually entered modern Parcel PIN that matches a Parcel object. Note that this one is for ManualCovenant records, while the other one is for attaching to ZooniverseSubject objects'''
    workflow = models.ForeignKey(
        ZooniverseWorkflow, on_delete=models.SET_NULL, null=True)
    manual_covenant = models.ForeignKey(
        ManualCovenant, on_delete=models.SET_NULL, null=True)

    # # These are kept separate of the foreign key relationship in case this needs to be reconnected later
    # zoon_subject_id = models.IntegerField(db_index=True, null=True, blank=True)
    # zoon_workflow_id = models.IntegerField(
    #     db_index=True, null=True, blank=True)

    parcel_pin = models.CharField(max_length=50, null=True, blank=True, db_index=True)

    date_added = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    comments = models.TextField(null=True, blank=True)

    # objects = CopyManager()

    def save(self, *args, **kwargs):
        self.workflow = self.manual_covenant.workflow
        # self.zoon_workflow_id = self.zooniverse_subject.workflow.zoon_id
        # self.zoon_subject_id = self.zooniverse_subject.zoon_subject_id
        super(ManualCovenantParcelPINLink, self).save(*args, **kwargs)
        self.manual_covenant.save()  # Does this really need to trigger every time? Seems so.


@receiver(models.signals.post_delete, sender=ManualCovenantParcelPINLink)
def model_delete(sender, instance, **kwargs):
    try:
        # instance.zooniverse_subject.get_final_values()
        instance.manual_covenant.save()
    except AttributeError:
        pass


SUPPORTING_DOC_TYPES = (
    ('Dd', 'Deed'),
    ('Ot', 'Other')
)


class ManualSupportingDocument(models.Model):
    '''An uploaded document that provides evidence of a racial covenant, which is attached to a ManualCovenant object.'''
    workflow = models.ForeignKey(
        ZooniverseWorkflow, on_delete=models.CASCADE, null=True)
    manual_covenant = models.ForeignKey(ManualCovenant, on_delete=models.CASCADE)
    doc_type = models.CharField(choices=SUPPORTING_DOC_TYPES, max_length=4, blank=True)
    doc_upload = models.FileField(
        storage=PublicMediaStorage(), upload_to="supporting_docs/", null=True)
    comments = models.TextField(blank=True)
    date_added = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
