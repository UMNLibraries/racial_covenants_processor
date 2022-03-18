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
        'workflow__workflow_name',
        'bool_covenant',
        'bool_problem',
        ('deed_date', DateRangeFilter)
    )

    inlines = [
        ResponseInline
    ]

    fieldsets = (
        (None, {
            'fields': (
                'zoon_subject_id', 'image_id', 'dt_retired',
                ('bool_covenant', 'bool_covenant_score'),
                ('covenant_text', 'covenant_text_score'),
            )
        }),
        ('Property fields', {
            'fields': (
                ('addition', 'addition_score'),
                ('block', 'block_score'),
                ('lot', 'lot_score'),
            ),
        }),
        ('Deed date', {
            'fields': (
                ('deed_date', 'deed_date_overall_score'),
                ('deed_date_year_score', 'deed_date_month_score', 'deed_date_day_score'),
                ),
        }),
    )

    readonly_fields = ['workflow', 'zoon_subject_id', 'dt_retired',
                       'image_id', 'bool_covenant_score', 'covenant_text_score', 'addition_score', 'block_score', 'lot_score', 'deed_date_overall_score', 'deed_date_year_score', 'deed_date_month_score', 'deed_date_day_score', ]

    # If you would like to add a default range filter
    # method pattern "get_rangefilter_{field_name}_default"
    def get_rangefilter_deed_date_default(self, request):
        return (datetime.date(1900, 1, 1), datetime.date(1970, 12, 31))

    # If you would like to change a title range filter
    # method pattern "get_rangefilter_{field_name}_title"
    def get_rangefilter_deed_date_title(self, request, field_path):
        return 'Deed date'


admin.site.enable_nav_sidebar = False
