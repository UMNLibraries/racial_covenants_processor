import datetime

from django.contrib import admin
from rangefilter.filters import DateRangeFilter

from zoon.models import ZooniverseResponseProcessed, ZooniverseSubject


class ResponseInline(admin.TabularInline):
    model = ZooniverseResponseProcessed

    extra = 0

    exclude = ['classification_id', 'response_raw',
               'workflow', 'user_id', 'created_at']

    readonly_fields = ['bool_covenant', 'covenant_text', 'addition', 'lot', 'block', 'seller',
                       'buyer', 'deed_date_year', 'deed_date_month', 'deed_date_day', 'user_name', 'created_at']


@admin.register(ZooniverseSubject)
class SubjectAdmin(admin.ModelAdmin):
    search_fields = ['zoon_subject_id',
                     'addition', 'covenant_text', 'image_id']

    list_display = ('__str__', 'bool_covenant', 'bool_problem',
                    'addition', 'lot', 'block', 'deed_date',)

    list_filter = (
        'bool_covenant', 'bool_problem',
        ('deed_date', DateRangeFilter)
    )

    inlines = [
        ResponseInline
    ]

    readonly_fields = ['zoon_subject_id', 'dt_retired', 'image_id']

    # If you would like to add a default range filter
    # method pattern "get_rangefilter_{field_name}_default"
    def get_rangefilter_deed_date_default(self, request):
        return (datetime.date(1900, 1, 1), datetime.date(1970, 12, 31))

    # If you would like to change a title range filter
    # method pattern "get_rangefilter_{field_name}_title"
    def get_rangefilter_deed_date_title(self, request, field_path):
        return 'Deed date'


admin.site.enable_nav_sidebar = False
