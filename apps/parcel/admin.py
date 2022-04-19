from django.contrib import admin

from .models import Parcel


@admin.register(Parcel)
class ParcelAdmin(admin.ModelAdmin):
    exclude = ['geom_4326']
    list_display = ['pin_primary', 'plat_name', 'plat', 'workflow']
    search_fields = ['plat_name']
    readonly_fields = ['geom_4326', 'plat']
