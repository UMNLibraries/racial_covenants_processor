import datetime

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from rangefilter.filters import DateRangeFilter

from zoon.models import ZooniverseResponseProcessed, ZooniverseSubject


class ResponseInline(admin.TabularInline):
    model = ZooniverseResponseProcessed

    extra = 0

    exclude = ['classification_id', 'response_raw',
               'workflow', 'user_id', 'created_at']

    readonly_fields = ['bool_covenant', 'covenant_text', 'addition', 'lot', 'block', 'seller',
                       'buyer', 'deed_date_year', 'deed_date_month', 'deed_date_day', 'user_name', 'created_at']


class ScoreRangeListFilter(admin.SimpleListFilter):
    title = _('median score')
    # Variable name to use for filtering queryset, and parameter for the filter that will be used in the URL query.
    parameter_name = 'median_score'

    def lookups(self, request, model_admin):
        return (
            ('<20', _('Under 20%')),
            ('20pct', _('20%')),
            ('40pct', _('40%')),
            ('60pct', _('60%')),
            ('80pct', _('80%')),
            ('100pct', _('100%')),
            ('100+', _('Over 100%')),
        )

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """

        if self.value() == '<20':
            return queryset.filter(**{
                f'{self.parameter_name}__lt': 0.2
            })

        if self.value() == '100+':
            return queryset.filter(**{
                f'{self.parameter_name}__gt': 1
            })

        # Loop through range. Generally based on 5 classifications.
        max_value = 0
        bool_first = True
        while max_value <= 1:
            next_max = max_value + 0.2
            if self.value() == f'{int(max_value*100)}pct':
                return queryset.filter(**{
                    f'{self.parameter_name}__gte': max_value,
                    f'{self.parameter_name}__lt': next_max,
                })
            max_value = next_max


class DateScoreRangeListFilter(ScoreRangeListFilter):
    title = _('date score')
    parameter_name = 'deed_date_overall_score'


class AdditionScoreRangeListFilter(ScoreRangeListFilter):
    title = _('addition score')
    parameter_name = 'addition_score'


@ admin.register(ZooniverseSubject)
class SubjectAdmin(admin.ModelAdmin):
    search_fields = ['zoon_subject_id',
                     'addition', 'covenant_text', 'image_id']

    list_display = ('__str__', 'bool_covenant', 'median_score', 'bool_problem',
                    'addition', 'lot', 'block', 'deed_date',)

    list_filter = (
        'workflow__workflow_name',
        'bool_covenant',
        'bool_problem',
        ('deed_date', DateRangeFilter),
        ScoreRangeListFilter,
        AdditionScoreRangeListFilter,
        DateScoreRangeListFilter,
        )

    inlines = [
        ResponseInline
        ]

    fieldsets = (
        (None, {
            'fields': (
                'zoon_subject_id', 'image_id', 'dt_retired',
                'median_score',
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
                ('deed_date_year_score',
                 'deed_date_month_score', 'deed_date_day_score'),
                ),
            }),
        )

    readonly_fields = ['workflow', 'zoon_subject_id', 'dt_retired',
                       'image_id', 'median_score', 'bool_covenant_score', 'covenant_text_score', 'addition_score', 'block_score', 'lot_score', 'deed_date_overall_score', 'deed_date_year_score', 'deed_date_month_score', 'deed_date_day_score', ]

    # If you would like to add a default range filter
    # method pattern "get_rangefilter_{field_name}_default"
    def get_rangefilter_deed_date_default(self, request):
        return (datetime.date(1900, 1, 1), datetime.date(1970, 12, 31))

    # If you would like to change a title range filter
    # method pattern "get_rangefilter_{field_name}_title"
    def get_rangefilter_deed_date_title(self, request, field_path):
        return 'Deed date'


admin.site.enable_nav_sidebar = False
