from django.contrib import admin
from django.db.models import Count

from .models import Plat, PlatMapPage, PlatAlternateName


class PlatMapPageInline(admin.TabularInline):
    model = PlatMapPage
    extra = 0
    exclude = ['workflow', 'page_image_web', ]
    readonly_fields = ['thumbnail_preview', 'remote_link', 'page_num']

    def thumbnail_preview(self, obj):
        return obj.thumbnail_preview

    thumbnail_preview.short_description = 'Thumbnail Preview'
    thumbnail_preview.allow_tags = True


@admin.register(Plat)
class PlatAdmin(admin.ModelAdmin):
    readonly_fields = ('workflow', 'plat_name')
    list_filter = ['workflow']
    list_display = ['plat_name', 'map_pages']
    search_fields = ['plat_name']
    inlines = [PlatMapPageInline]

    def map_pages(self, obj):
        return obj.map_pages

    map_pages.admin_order_field = 'map_pages'

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(map_pages=Count("platmappage"))
        return queryset


@admin.register(PlatAlternateName)
class PlatAlternateNameAdmin(admin.ModelAdmin):
    list_filter = ['workflow']
    list_display = ['alternate_name', 'plat_name', 'workflow']
    autocomplete_fields = ['plat']
    exclude = ['plat_name']
    readonly_fields = ['alternate_name_standardized']
    search_fields = ['alternate_name', 'plat__plat_name']
