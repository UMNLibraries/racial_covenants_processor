from django.contrib import admin
from rangefilter.filters import DateRangeFilter

from .models import DeedPage, SearchHitReport

@admin.register(SearchHitReport)
class SearchHitReportAdmin(admin.ModelAdmin):
    list_filter = ['workflow']
    list_display = ['__str__', 'created_at', 'num_hits']

    readonly_fields = ['workflow', 'report_csv', 'num_hits', 'created_at']


@admin.register(DeedPage)
class DeedPageAdmin(admin.ModelAdmin):
    show_full_result_count = False
    list_filter = ['workflow', 'workflow__workflow_name', 'bool_match', 'bool_exception', 'matched_terms__term', ('doc_date', DateRangeFilter),]
    list_display = ['doc_num', 'bool_match', 'bool_exception', 'get_matched_terms', 'book_id', 'page_num', 'split_page_num', 's3_lookup', 'zooniverse_subject']
    list_select_related = ['workflow']
    search_fields = ['doc_num', 's3_lookup', 'book_id']
    readonly_fields = (
        'workflow',
        'bool_match',
        'bool_manual',
        'bool_exception',
        'doc_num',
        'book_id',
        'page_num',
        'split_page_num',
        'doc_page_count',
        'doc_date',
        'doc_alt_id',
        'batch_id',
        'thumbnail_preview',
        'prev_thumbnail_preview',
        'next_thumbnail_preview',
        # 'zooniverse_subject',
        'zooniverse_subject_1st_page',
        'zooniverse_subject_2nd_page',
        'zooniverse_subject_3rd_page',
        's3_lookup',
        'doc_type',
        'page_stats',
        'page_ocr_text',
        'page_ocr_json',
        'public_uuid',
        'matched_terms'
    )
    exclude = ['page_image_web', 'prev_page_image_web', 'next_page_image_web', 'next_next_page_image_web', 'page_image_web_highlighted', 'prev_deedpage', 'next_deedpage', 'next_next_deedpage', 'prev_page_image_lookup', 'next_page_image_lookup', 'next_next_page_image_lookup', 'zooniverse_subject']

    def get_queryset(self, request):
        qs = super().get_queryset(request).defer('page_stats', 'page_ocr_json', 'page_ocr_text', 'zooniverse_subject', 'doc_alt_id', 'public_uuid', 'page_image_web')
        return qs

    def thumbnail_preview(self, obj):
        return obj.thumbnail_preview

    thumbnail_preview.short_description = 'Thumbnail Preview'
    thumbnail_preview.allow_tags = True

    def prev_thumbnail_preview(self, obj):
        return obj.prev_thumbnail_preview

    prev_thumbnail_preview.short_description = 'Previous page'
    prev_thumbnail_preview.allow_tags = True

    def next_thumbnail_preview(self, obj):
        return obj.next_thumbnail_preview

    next_thumbnail_preview.short_description = 'Next page(s)'
    next_thumbnail_preview.allow_tags = True

    def get_matched_terms(self, obj):
        if obj.bool_match or obj.bool_exception:
            return ", ".join([d.term for d in obj.matched_terms.all()])
        return ''

    get_matched_terms.short_description = 'Matched terms'
