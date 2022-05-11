from django.contrib import admin

from .models import Parcel


@admin.register(Parcel)
class ParcelAdmin(admin.ModelAdmin):
    exclude = ['geom_4326']
    list_filter = ['workflow', 'city']
    list_display = ['pin_primary', 'plat_name', 'plat', 'street_address', 'city']
    search_fields = ['plat_name', 'pin_primary', 'street_address', 'city']
    # readonly_fields = ['geom_4326', 'plat']

    def get_readonly_fields(self, request, obj=None):
        '''Make all fields read-only'''
        return [f.name for f in self.model._meta.fields]
