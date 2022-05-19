import json
from django.contrib.gis.db import models
from django.contrib.gis.db.models.aggregates import Union
from django.contrib.gis import geos
from django.dispatch import receiver
from django.utils.text import slugify

from postgres_copy import CopyManager

from apps.parcel.utils.parcel_utils import build_parcel_spatial_lookups, gather_all_covenant_candidates


class ZooniverseWorkflow(models.Model):
    zoon_id = models.IntegerField(null=True, db_index=True)
    workflow_name = models.CharField(max_length=100, db_index=True)
    version = models.FloatField(null=True)

    def __str__(self):
        return f"{self.workflow_name} ({self.version})"

    @property
    def slug(self):
        return slugify(self.workflow_name)


MATCH_TYPE_OPTIONS = (
    ('SL', 'Simple lot'),
    ('ML', 'Multiple single lots'),
    ('PL', 'Partial lot'),
    ('PD', 'Long phys description'),
    ('C', 'Cemetery plot'),
    ('PC', 'Petition covenant'),
    ('SE', 'Something else'),
    ('NG', 'No geographic information'),
)


class ZooniverseSubject(models.Model):
    '''Future: Assign an id to correspond to a deed image pre-Zooniverse'''
    workflow = models.ForeignKey(ZooniverseWorkflow, on_delete=models.CASCADE)
    zoon_subject_id = models.IntegerField(db_index=True)

    image_ids = models.JSONField(blank=True)

    dt_retired = models.DateTimeField(null=True)

    # This part comes from the reducers
    bool_covenant = models.BooleanField(null=True)
    bool_problem = models.BooleanField(default=False)
    covenant_text = models.TextField(blank=True)
    addition = models.CharField(max_length=500, blank=True)
    lot = models.TextField(blank=True)
    block = models.CharField(max_length=500, blank=True)
    seller = models.CharField(max_length=100, blank=True)
    buyer = models.CharField(max_length=100, blank=True)
    deed_date = models.DateField(null=True)

    # Match type not a part of Ramsey County workflow but will be used in future.
    match_type = models.CharField(choices=MATCH_TYPE_OPTIONS, max_length=4, null=True, blank=True)

    # Scores, also from the reducers
    bool_covenant_score = models.FloatField(null=True)
    covenant_text_score = models.FloatField(null=True)
    addition_score = models.FloatField(null=True)
    lot_score = models.FloatField(null=True)
    block_score = models.FloatField(null=True)
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
    seller_final = models.CharField(
        max_length=100, null=True, blank=True, verbose_name="Seller name")
    buyer_final = models.CharField(
        max_length=100, null=True, blank=True, verbose_name="Buyer name")
    deed_date_final = models.DateField(
        null=True, blank=True, verbose_name="Deed date")

    street_address_final = models.TextField(null=True, blank=True, verbose_name="Street address")
    city_final = models.CharField(
        max_length=500, null=True, blank=True, verbose_name="City")
    match_type_final = models.CharField(choices=MATCH_TYPE_OPTIONS, max_length=4, null=True, blank=True)

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

    def __str__(self):
        return f"{self.workflow} {self.zoon_subject_id}"

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

    def get_parcel_addresses(self):
        return list(self.parcel_matches.all().values('street_address', 'city', 'state', 'zip_code'))

    def get_parcel_cities(self):
        return self.parcel_matches.all().values_list('city', flat=True)

    def set_addresses(self):
        if self.bool_parcel_match:
            self.parcel_addresses = json.dumps(self.get_parcel_addresses())
            cities = self.get_parcel_cities()
            if len(cities) > 0:
                # Assuming for the most part that we can generally take the first city we find. There will be edge cases, but those can be accessed via the address JSON object and this one is more of a shorthand
                self.parcel_city = cities[0]

    def set_geom_union(self):
        if self.bool_parcel_match:
            self.geom_union_4326 = self.get_geom_union()

    def check_bool_manual_update(self):
        if self.manualcorrection_set.count() > 0:
            self.bool_manual_correction = True
        else:
            self.bool_manual_correction = False

    def get_final_value(self, attr, blank_value=""):
        if self.manualcorrection_set.count() > 0:
            if getattr(self.manualcorrection_set.first(), attr) not in [None, blank_value]:
                return getattr(self.manualcorrection_set.first(), attr)
        return getattr(self, attr)

    def get_from_parcel_or_cx(self, attr, blank_value=""):
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
        self.seller_final = self.get_final_value('seller')
        self.buyer_final = self.get_final_value('buyer')
        self.match_type_final = self.get_final_value('match_type')
        self.deed_date_final = self.get_final_value('deed_date', None)

        self.street_address_final = self.get_from_parcel_or_cx(
            'street_address')
        self.city_final = self.get_from_parcel_or_cx('city')

    def check_parcel_match(self):
        self.parcel_matches.clear()
        self.bool_parcel_match = False
        parcel_lookup = None
        join_strings = []
        # Main parcel
        if self.lot_final != '':
            parcel_lookup = build_parcel_spatial_lookups(self.workflow)
            self.join_candidates = gather_all_covenant_candidates(self)
            print(self.join_candidates)

            for c in self.join_candidates:
                join_strings.append(c['join_string'])
                try:
                    lot_match = parcel_lookup[c['join_string']] # TODO: There can be more than one modern parcel with same lot designation -- weird!
                    print(f"MATCH: {c['join_string']}")

                    self.parcel_matches.add(lot_match['parcel_id'])
                    self.bool_parcel_match = True
                except:
                    print(f"NO MATCH: {c['join_string']}")

    def save(self, *args, **kwargs):
        self.get_final_values()
        self.check_parcel_match()
        self.set_geom_union()
        self.set_addresses()
        super(ZooniverseSubject, self).save(*args, **kwargs)


class ZooniverseResponseRaw(models.Model):
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
    workflow = models.ForeignKey(ZooniverseWorkflow, on_delete=models.CASCADE)
    classification_id = models.IntegerField()
    user_name = models.CharField(max_length=100, blank=True, db_index=True)
    user_id = models.IntegerField(null=True, db_index=True)
    subject = models.ForeignKey(
        ZooniverseSubject, null=True, on_delete=models.SET_NULL)
    bool_covenant = models.CharField(max_length=100, null=True, blank=True)
    covenant_text = models.TextField(blank=True)
    addition = models.CharField(max_length=500, blank=True)
    lot = models.TextField(blank=True)
    block = models.CharField(max_length=500, blank=True)
    seller = models.CharField(max_length=100, blank=True)
    buyer = models.CharField(max_length=100, blank=True)
    deed_date_year = models.CharField(max_length=10, blank=True)
    deed_date_month = models.CharField(max_length=100, blank=True)
    deed_date_day = models.CharField(max_length=10, blank=True)
    created_at = models.DateTimeField()
    response_raw = models.ForeignKey(
        ZooniverseResponseRaw, on_delete=models.CASCADE, null=True)


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
    seller = models.CharField(max_length=100, null=True, blank=True)
    buyer = models.CharField(max_length=100, null=True, blank=True)
    deed_date = models.DateField(null=True, blank=True)

    street_address = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)

    date_added = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    match_type = models.CharField(choices=MATCH_TYPE_OPTIONS, max_length=4, null=True, blank=True)
    comments = models.TextField(null=True, blank=True)

    objects = CopyManager()

    def save(self, *args, **kwargs):
        self.workflow = self.zooniverse_subject.workflow
        self.zoon_workflow_id = self.zooniverse_subject.workflow.zoon_id
        self.zoon_subject_id = self.zooniverse_subject.zoon_subject_id
        super(ManualCorrection, self).save(*args, **kwargs)

        # self.zooniverse_subject.get_final_values()
        self.zooniverse_subject.save()


class ExtraParcelCandidate(models.Model):
    '''For use when property spans more than one block or addition, NOT for multiple lots in same addition/block for the moment'''
    workflow = models.ForeignKey(
        ZooniverseWorkflow, on_delete=models.SET_NULL, null=True)
    zooniverse_subject = models.ForeignKey(
        ZooniverseSubject, on_delete=models.SET_NULL, null=True)

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
        self.zooniverse_subject.save()


@receiver(models.signals.post_delete, sender=ManualCorrection)
def model_delete(sender, instance, **kwargs):
    instance.zooniverse_subject.get_final_values()
    instance.zooniverse_subject.save()
