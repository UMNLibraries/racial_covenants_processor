from django.contrib import admin
from rangefilter.filters import DateRangeFilter

from .models import DeedPage, SearchHitReport

@admin.register(SearchHitReport)
class SearchHitReportAdmin(admin.ModelAdmin):
    list_filter = ['workflow']
    list_display = ['__str__', 'created_at', 'num_hits']

    readonly_fields = ['workflow', 'report_csv', 'num_hits', 'created_at']

    # workflow = models.ForeignKey(
    #     ZooniverseWorkflow, on_delete=models.CASCADE, null=True)
    # report_csv = models.FileField(
    #     storage=PublicMediaStorage(), upload_to="analysis/", null=True)
    # num_hits = models.IntegerField(null=True)
    # created_at = models.DateTimeField()

@admin.register(DeedPage)
class DeedPageAdmin(admin.ModelAdmin):
    show_full_result_count = False
    list_filter = ['workflow', 'bool_match', 'bool_exception', 'matched_terms__term', ('doc_date', DateRangeFilter), 'doc_type',]
    list_display = ['doc_num', 'bool_match', 'bool_exception', 'get_matched_terms', 's3_lookup', 'page_num', 'page_image_web', 'zooniverse_subject']
    search_fields = ['doc_num']
    readonly_fields = (
        'workflow',
        'bool_match',
        'bool_exception',
        'thumbnail_preview',
        'zooniverse_subject',
        'doc_num',
        'page_num',
        'doc_date',
        's3_lookup',
        'doc_type',
        'page_stats',
        'page_ocr_text',
        'page_ocr_json',
        'matched_terms'
    )
    exclude = ['page_image_web']

    def thumbnail_preview(self, obj):
        return obj.thumbnail_preview

    thumbnail_preview.short_description = 'Thumbnail Preview'
    thumbnail_preview.allow_tags = True

    def get_matched_terms(self, obj):
        if obj.bool_match or obj.bool_exception:
            return ", ".join([d.term for d in obj.matched_terms.all()])
        return ''

    get_matched_terms.short_description = 'Matched terms'
