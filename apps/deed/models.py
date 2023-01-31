from django.db import models
from django.db.models import OuterRef, Subquery, Case, When, Count, Q
from django.contrib.postgres.aggregates import StringAgg
from django.utils.html import mark_safe
from postgres_copy import CopyManager

from racial_covenants_processor.storage_backends import PrivateMediaStorage, PublicMediaStorage, PublicDeedStorage
from apps.zoon.models import ZooniverseWorkflow, ZooniverseSubject


class MatchTerm(models.Model):
    term = models.CharField(max_length=100, db_index=True)

    def __str__(self):
        return self.term

class HitsDeedPageManager(models.Manager):
    '''This is a heavy-lifting manager to tag deedpages with the previous and next images, which will hopefully eliminate replicating this logic elsewhere. Note: It only returns DeedPage results where bool_match=True'''

    def get_queryset(self):
        # # TODO: Move a lot of this to model itself and save on import, calculating all the doc num counts beforehand to save time
        # # Subquery for counting all pages
        # doc_page_count = DeedPage.objects.filter(
        #     workflow=OuterRef('workflow'),
        #     doc_num=OuterRef('doc_num')
        # ).values(
        #     'doc_num'
        # ).annotate(
        #     c=Count('*')
        # ).values(
        #     'c'
        # )[:1]

        return super().get_queryset().filter(bool_match=True).annotate(
        #     page_count=Subquery(doc_page_count)
        # ).annotate(
            matched_terms_list=StringAgg('matched_terms__term', delimiter=', ')
        ).annotate(
            prev_page_image_web=Case(
                # same doc num with multiple pages + splitpage
                When(
                    Q(doc_page_count__gt=1) & Q(split_page_num__gte=1), then=Subquery(
                        DeedPage.objects.filter(workflow=OuterRef('workflow'), doc_num=OuterRef('doc_num'), split_page_num=OuterRef('split_page_num') - 1).order_by('-pk').values('page_image_web')[:1]
                    )
                ),
                # no doc_num, book and page only, splitpage
                When(
                    Q(doc_page_count=1) & Q(split_page_num__gte=1), then=Subquery(
                        DeedPage.objects.filter(workflow=OuterRef('workflow'), book_id=OuterRef('book_id'), split_page_num=OuterRef('split_page_num') - 1).order_by('-pk').values('page_image_web')[:1]
                    )
                ),
                # no doc_num, book and page only, no splitpage
                When(
                    Q(doc_page_count=1), then=Subquery(
                        DeedPage.objects.filter(workflow=OuterRef('workflow'), book_id=OuterRef('book_id'), page_num=OuterRef('page_num') - 1).order_by('-pk').values('page_image_web')[:1]
                    )
                ),
                default=Subquery(
                    # same doc num with multiple pages
                    DeedPage.objects.filter(workflow=OuterRef('workflow'), doc_num=OuterRef('doc_num'), page_num=OuterRef('page_num') - 1).order_by('-pk').values('page_image_web')[:1]
                )
            ),
            next_page_image_web=Case(
                # same doc num with multiple pages + splitpage
                When(
                    Q(doc_page_count__gt=1) & Q(split_page_num__gte=1), then=Subquery(
                        DeedPage.objects.filter(workflow=OuterRef('workflow'), doc_num=OuterRef('doc_num'), split_page_num=OuterRef('split_page_num') + 1).order_by('-pk').values('page_image_web')[:1]
                    )
                ),
                # no doc_num, book and page only, splitpage
                When(
                    Q(doc_page_count=1) & Q(split_page_num__gte=1), then=Subquery(
                        DeedPage.objects.filter(workflow=OuterRef('workflow'), book_id=OuterRef('book_id'), split_page_num=OuterRef('split_page_num') + 1).order_by('-pk').values('page_image_web')[:1]
                    )
                ),
                # no doc_num, book and page only, no splitpage
                When(
                    Q(doc_page_count=1), then=Subquery(
                        DeedPage.objects.filter(workflow=OuterRef('workflow'), book_id=OuterRef('book_id'), page_num=OuterRef('page_num') + 1).order_by('-pk').values('page_image_web')[:1]
                    )
                ),
                default=Subquery(
                    # same doc num with multiple pages
                    DeedPage.objects.filter(workflow=OuterRef('workflow'), doc_num=OuterRef('doc_num'), page_num=OuterRef('page_num') + 1).order_by('-pk').values('page_image_web')[:1]
                )
            ),
            next_next_page_image_web=Case(
                # same doc num with multiple pages + splitpage
                When(
                    Q(doc_page_count__gt=1) & Q(split_page_num__gte=1), then=Subquery(
                        DeedPage.objects.filter(workflow=OuterRef('workflow'), doc_num=OuterRef('doc_num'), split_page_num=OuterRef('split_page_num') + 2).order_by('-pk').values('page_image_web')[:1]
                    )
                ),
                # no doc_num, book and page only, splitpage
                When(
                    Q(doc_page_count=1) & Q(split_page_num__gte=1), then=Subquery(
                        DeedPage.objects.filter(workflow=OuterRef('workflow'), book_id=OuterRef('book_id'), split_page_num=OuterRef('split_page_num') + 2).order_by('-pk').values('page_image_web')[:1]
                    )
                ),
                # no doc_num, book and page only, no splitpage
                When(
                    Q(doc_page_count=1), then=Subquery(
                        DeedPage.objects.filter(workflow=OuterRef('workflow'), book_id=OuterRef('book_id'), page_num=OuterRef('page_num') + 2).order_by('-pk').values('page_image_web')[:1]
                    )
                ),
                default=Subquery(
                    # same doc num with multiple pages
                    DeedPage.objects.filter(workflow=OuterRef('workflow'), doc_num=OuterRef('doc_num'), page_num=OuterRef('page_num') + 2).order_by('-pk').values('page_image_web')[:1]
                )
            )
        )


class DeedPage(models.Model):
    workflow = models.ForeignKey(
        ZooniverseWorkflow, on_delete=models.CASCADE, null=True)
    s3_lookup = models.CharField(blank=True, max_length=500, db_index=True)
    doc_num = models.CharField(blank=True, max_length=100, db_index=True)
    doc_alt_id = models.CharField(blank=True, max_length=100, db_index=True)
    batch_id = models.CharField(blank=True, max_length=255)
    book_id = models.CharField(blank=True, max_length=100, db_index=True)
    page_num = models.IntegerField(null=True)
    split_page_num = models.IntegerField(null=True)  # Alternate page numbering that happens when a multipage image file has been split by the ingestion process
    doc_date = models.DateField(null=True, db_index=True)
    doc_type = models.CharField(blank=True, max_length=100)
    public_uuid = models.CharField(blank=True, max_length=50, db_index=True)
    page_image_web = models.ImageField(
        storage=PublicDeedStorage(), max_length=200, null=True)
    page_stats = models.FileField(
        storage=PrivateMediaStorage(), max_length=200, null=True)
    page_ocr_text = models.FileField(
        storage=PrivateMediaStorage(), max_length=200, null=True)
    page_ocr_json = models.FileField(
        storage=PrivateMediaStorage(), max_length=200, null=True)
    bool_match = models.BooleanField(default=False, db_index=True)
    bool_exception = models.BooleanField(default=False, db_index=True)
    matched_terms = models.ManyToManyField(MatchTerm)

    # These fields aid in setting up Zooniverse images
    doc_page_count = models.IntegerField(null=True)
    # prev_page_image_web = models.ImageField(
    #     storage=PublicDeedStorage(), max_length=200, null=True)
    # next_page_image_web = models.ImageField(
    #     storage=PublicDeedStorage(), max_length=200, null=True)
    # next_next_page_image_web = models.ImageField(
    #     storage=PublicDeedStorage(), max_length=200, null=True)

    zooniverse_subject = models.ForeignKey(
        ZooniverseSubject, on_delete=models.SET_NULL, null=True)

    objects = models.Manager()
    hit_objects = HitsDeedPageManager()

    class Meta:
        indexes = [
            models.Index(fields=['-id'], name='id_desc'),
            models.Index(fields=['-id', 'workflow_id'], name='id_workflow_index'),
            models.Index(fields=['workflow_id', '-id'], name='workflow_id_index'),
            models.Index(fields=['workflow_id'], name='workflow_only_index')
        ]

    @property
    def thumbnail_preview(self):
        if self.page_image_web:
            return mark_safe(f'<a href="{self.page_image_web.url}" target="_blank"><img src="{self.page_image_web.url}" width="100" /></a>')
        return ""

    # Need to save through private media storage in gather_deed_images.py
    # @property
    # def page_ocr_text_link(self):
    #     if self.page_image_web:
    #         return mark_safe(f'<a href="{self.page_image_web.url}" target="_blank"><img src="{self.page_image_web.url}" width="100" /></a>')
    #     return ""


class SearchHitReport(models.Model):
    workflow = models.ForeignKey(
        ZooniverseWorkflow, on_delete=models.CASCADE, null=True)
    report_csv = models.FileField(
        storage=PublicMediaStorage(), upload_to="analysis/", null=True)
    num_hits = models.IntegerField(null=True)
    created_at = models.DateTimeField()

    def __str__(self):
        return f"{self.workflow.workflow_name}, {self.created_at}"
