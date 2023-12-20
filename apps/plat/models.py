# from django.db import models
from django.contrib.gis.db import models
from django.utils.text import slugify
from django.utils.html import mark_safe
from django.db.models import F

from apps.parcel.utils.parcel_utils import standardize_addition, get_all_parcel_options, build_parcel_spatial_lookups
from racial_covenants_processor.storage_backends import PrivateMediaStorage

from postgres_copy import CopyManager


class Plat(models.Model):
    workflow = models.ForeignKey(
        'zoon.ZooniverseWorkflow', null=True, on_delete=models.SET_NULL)
    plat_name = models.CharField(max_length=255, db_index=True, null=True)
    plat_year = models.IntegerField(null=True, blank=True)
    book_name = models.CharField(
        max_length=255, db_index=True, null=True, blank=True)
    gov_id = models.CharField(
        max_length=255, null=True, blank=True)  # Can't be an index because some plat maps have multiple plats on same map page. Maybe revisit this later
    plat_name_standardized = models.CharField(
        max_length=255, db_index=True, null=True)

    class Meta:
        ordering = ["plat_name"]

    def slug(self):
        return slugify(f"{self.workflow.slug} {self.name}")

    def __str__(self):
        return self.plat_name

    def save(self, *args, **kwargs):
        self.plat_name_standardized = self.standardize_addition(
            self.plat_name)


class PlatMapPage(models.Model):
    plat = models.ForeignKey(Plat, on_delete=models.CASCADE)
    page_num = models.IntegerField(null=True)
    remote_link = models.URLField(blank=True)
    page_image_web = models.ImageField(
        storage=PrivateMediaStorage(), null=True)

    @property
    def thumbnail_preview(self):
        print(self.page_image_web)
        if self.page_image_web:
            return mark_safe(f'<a href="{self.page_image_web.url}" target="_blank"><img src="{self.page_image_web.url}" width="100" /></a>')
        return ""


class PlatAlternateName(models.Model):
    workflow = models.ForeignKey(
        'zoon.ZooniverseWorkflow', null=True, on_delete=models.SET_NULL)
    plat = models.ForeignKey(Plat, null=True, on_delete=models.SET_NULL)

    # These are kept separate of the foreign key relationship in case this needs to be reconnected later
    zoon_workflow_id = models.IntegerField(
        db_index=True, null=True, blank=True)
    plat_name = models.CharField(
        max_length=255, db_index=True, null=True, blank=True)

    alternate_name = models.CharField(max_length=255, db_index=True, null=True)
    alternate_name_standardized = models.CharField(
        max_length=255, db_index=True, null=True)

    objects = CopyManager()

    def save(self, *args, **kwargs):
        from apps.parcel.models import Parcel, ParcelJoinCandidate
        from apps.zoon.models import ZooniverseSubject, ManualCovenant
        self.plat_name = self.plat.plat_name
        self.zoon_workflow_id = self.plat.workflow.zoon_id
        self.alternate_name_standardized = standardize_addition(
            self.alternate_name)

        super(PlatAlternateName, self).save(*args, **kwargs)

        parcel_matches = Parcel.objects.filter(
            workflow=self.workflow,
            plat_standardized=self.alternate_name_standardized
        )
        parcel_matches.update(plat=self.plat)

        plat_parcels = Parcel.objects.filter(
            workflow=self.workflow,
            plat=self.plat
        )

        # avoid duplication
        ParcelJoinCandidate.objects.filter(
            parcel__pk__in=plat_parcels.values_list('pk', flat=True)
        ).delete()

        # update parcel candidates for all parcels in this plat
        join_cands = []
        for parcel in plat_parcels:
            candidates = get_all_parcel_options(parcel)
            for c in candidates:
                # parcel_spatial_lookup[c['join_string']] = c
                join_cands.append(ParcelJoinCandidate(
                    workflow=self.workflow,
                    parcel=parcel,
                    plat_name_standardized=parcel.plat_standardized,
                    join_string=c['join_string'],
                    metadata=c['metadata']
                ))
        ParcelJoinCandidate.objects.bulk_create(join_cands, batch_size=5000)

        print(self.alternate_name)
        parcel_lookup = build_parcel_spatial_lookups(self.workflow)
        for z in ZooniverseSubject.objects.filter(workflow=self.workflow, addition_final__iexact=self.alternate_name):
            z.save(parcel_lookup=parcel_lookup)

        for m in ManualCovenant.objects.filter(workflow=self.workflow, addition__iexact=self.alternate_name):
            m.save(parcel_lookup=parcel_lookup)


class Subdivision(models.Model):
    '''This is presumed to be a modern Subdivision GIS layer (as opposed to a plat map), but there may be other uses'''
    workflow = models.ForeignKey(
        'zoon.ZooniverseWorkflow', null=True, on_delete=models.SET_NULL)
    feature_id = models.IntegerField(null=True)
    name = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    name_standardized = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    doc_num = models.CharField(blank=True, null=True, max_length=100, db_index=True)
    recorded_date = models.DateField(null=True, db_index=True)
    orig_data = models.JSONField(null=True, blank=True)
    orig_filename = models.CharField(max_length=255, null=True, blank=True)
    geom_4326 = models.MultiPolygonField(srid=4326)

    class Meta:
        ordering = ["name"]

    def slug(self):
        return slugify(f"{self.workflow.slug} {self.name}")

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.name_standardized = self.standardize_addition(
            self.name)


class SubdivisionAlternateName(models.Model):
    workflow = models.ForeignKey(
        'zoon.ZooniverseWorkflow', null=True, on_delete=models.SET_NULL)
    subdivision = models.ForeignKey(Subdivision, null=True, on_delete=models.SET_NULL)

    # These are kept separate of the foreign key relationship in case this needs to be reconnected later
    zoon_workflow_id = models.IntegerField(
        db_index=True, null=True, blank=True)
    subdivision_name = models.CharField(
        max_length=255, db_index=True, null=True, blank=True)

    alternate_name = models.CharField(max_length=255, db_index=True, null=True)
    alternate_name_standardized = models.CharField(
        max_length=255, db_index=True, null=True)

    objects = CopyManager()

    def save(self, *args, **kwargs):
        from apps.parcel.models import Parcel, ParcelJoinCandidate
        from apps.zoon.models import ZooniverseSubject, ManualCovenant
        self.subdivision_name = self.subdivision.name
        self.zoon_workflow_id = self.subdivision.workflow.zoon_id
        self.alternate_name_standardized = standardize_addition(
            self.alternate_name)

        super(SubdivisionAlternateName, self).save(*args, **kwargs)

        parcel_matches = Parcel.objects.filter(
            workflow=self.workflow,
            plat_standardized=self.alternate_name_standardized
        )

        parcel_matches.update(subdivision_spatial=self.subdivision)

        subdivision_parcels = Parcel.objects.filter(
            workflow=self.workflow,
            subdivision_spatial=self.subdivision
        )

        # avoid duplication
        ParcelJoinCandidate.objects.filter(
            parcel__pk__in=subdivision_parcels.values_list('pk', flat=True)
        ).delete()

        # update parcel candidates for all parcels in this plat
        join_cands = []
        for parcel in subdivision_parcels:
            candidates = get_all_parcel_options(parcel)
            for c in candidates:
                # parcel_spatial_lookup[c['join_string']] = c
                join_cands.append(ParcelJoinCandidate(
                    workflow=self.workflow,
                    parcel=parcel,
                    plat_name_standardized=parcel.plat_standardized,
                    join_string=c['join_string'],
                    metadata=c['metadata']
                ))
        ParcelJoinCandidate.objects.bulk_create(join_cands, batch_size=5000)

        # Re-save all zooniverse subjects with this alternate name
        print(self.alternate_name)
        parcel_lookup = build_parcel_spatial_lookups(self.workflow)
        for z in ZooniverseSubject.objects.filter(workflow=self.workflow, addition_final__iexact=self.alternate_name):
            z.save(parcel_lookup=parcel_lookup)

        for m in ManualCovenant.objects.filter(workflow=self.workflow, addition__iexact=self.alternate_name):
            m.save(parcel_lookup=parcel_lookup)
