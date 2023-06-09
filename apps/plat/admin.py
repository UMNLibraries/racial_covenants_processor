from django.contrib import admin
from django.db.models import Count, Q

from .models import Plat, PlatMapPage, PlatAlternateName, Subdivision, SubdivisionAlternateName


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
    list_display = ['plat_name', 'map_pages', 'linked_parcel_count']
    search_fields = ['plat_name']
    inlines = [PlatMapPageInline]

    def linked_parcel_count(self, obj):
        return obj.linked_parcel_count
    linked_parcel_count.admin_order_field = 'linked_parcel_count'

    def map_pages(self, obj):
        return obj.map_pages
    map_pages.admin_order_field = 'map_pages'

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(
            map_pages=Count("platmappage", distinct=True)
        ).annotate(
            linked_parcel_count=Count("parcel", distinct=True)
        )
        return queryset


@admin.register(PlatAlternateName)
class PlatAlternateNameAdmin(admin.ModelAdmin):
    list_filter = ['workflow']
    list_display = ['alternate_name', 'plat_name', 'workflow']
    autocomplete_fields = ['plat']
    exclude = ['plat_name', 'zoon_workflow_id']
    readonly_fields = ['alternate_name_standardized']
    search_fields = ['alternate_name', 'plat__plat_name']


@admin.register(Subdivision)
class SubdivisionAdmin(admin.ModelAdmin):
    readonly_fields = [
        'workflow',
        'feature_id',
        'doc_num',
        'name_standardized',
        'recorded_date',
        'name',
        'orig_data',
        'orig_filename',
        'geom_4326'
    ]
    list_filter = ['workflow']
    list_display = ['name', 'linked_parcel_count', 'covenanted_parcel_count']
    search_fields = ['name']

    def linked_parcel_count(self, obj):
        return obj.linked_parcel_count
    linked_parcel_count.admin_order_field = 'linked_parcel_count'

    def covenanted_parcel_count(self, obj):
        return obj.covenanted_parcel_count
    covenanted_parcel_count.admin_order_field = 'covenanted_parcel_count'

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(
            linked_parcel_count=Count("parcel", distinct=True)
        ).annotate(
            covenanted_parcel_count=Count('parcel', filter=Q(parcel__zooniversesubject=True))
        )
        return queryset


@admin.register(SubdivisionAlternateName)
class SubdivisionAlternateNameAdmin(admin.ModelAdmin):
    list_filter = ['workflow']
    list_display = ['alternate_name', 'subdivision_name', 'workflow']
    autocomplete_fields = ['subdivision']
    exclude = ['subdivision_name', 'zoon_workflow_id']
    readonly_fields = ['alternate_name_standardized']
    search_fields = ['alternate_name', 'subdivision__subdivision_name']
