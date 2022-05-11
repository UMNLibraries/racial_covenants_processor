from django.contrib import admin

from .models import DeedPage


@admin.register(DeedPage)
class DeedPageAdmin(admin.ModelAdmin):
    list_filter = ['workflow', 'bool_match']
    list_display = ['doc_num', 'bool_match', 'page_image_web', 'zooniverse_subject']
    search_fields = ['doc_num']
    readonly_fields = (
        'workflow',
        'bool_match',
        'thumbnail_preview',
        'zooniverse_subject',
        'doc_num',
        'page_num',
        'doc_date',
        'page_ocr_text'
    )
    exclude = ['page_image_web']

    def thumbnail_preview(self, obj):
        return obj.thumbnail_preview

    thumbnail_preview.short_description = 'Thumbnail Preview'
    thumbnail_preview.allow_tags = True
