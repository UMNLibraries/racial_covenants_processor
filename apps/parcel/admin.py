from django.contrib import admin

from .models import Parcel, ManualParcelCandidate


class ManualParcelCandidateInline(admin.StackedInline):
    model = ManualParcelCandidate
    extra = 0
    exclude = ['workflow', 'parcel_pin_primary']


@admin.register(Parcel)
class ParcelAdmin(admin.ModelAdmin):
    fields = [
        'workflow',
        'feature_id',
        'join_strings',
        'pin_primary',
        'pin_secondary',
        'street_address',
        'city',
        'state',
        'zip_code',
        'county_name',
        'county_fips',
        'plat',
        'plat_name',
        'plat_standardized',
        'subdivision_spatial',
        'block',
        'lot',
        'join_description',
        'phys_description',
        'township',
        'range',
        'section',
        'orig_filename',
    ]
    list_filter = ['workflow', 'city']
    list_display = ['pin_primary', 'street_address', 'plat', 'subdivision_spatial', 'city', 'plat_name', 'block', 'lot']
    search_fields = ['plat_name', 'pin_primary', 'street_address', 'city']
    # readonly_fields = ['geom_4326', 'plat']

    inlines = [
        ManualParcelCandidateInline
    ]

    def get_readonly_fields(self, request, obj=None):
        '''Make all fields read-only'''
        return [f.name for f in self.model._meta.fields] + ['join_strings']

    # def join_strings(self, obj):
    #     return obj.join_strings
    #
    # join_strings.short_description = 'Join strings'
    # # join_strings.allow_tags = True
