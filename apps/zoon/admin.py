import datetime

from django.contrib import admin
from django.urls import reverse, NoReverseMatch
from django.utils.html import mark_safe
from django.utils.translation import gettext_lazy as _

from rangefilter.filters import DateRangeFilter

from apps.deed.models import DeedPage
from apps.parcel.models import Parcel
from apps.zoon.models import ZooniverseWorkflow, ZooniverseResponseProcessed, ZooniverseSubject, ManualCorrection, ExtraParcelCandidate, ManualParcelPINLink, ManualCovenantParcelPINLink, ManualCovenant, ManualSupportingDocument


@admin.register(ZooniverseWorkflow)
class WorkflowAdmin(admin.ModelAdmin):
    pass


deed_page_exclude_fields = ['workflow', 'page_image_web', 'page_image_web_highlighted', 'page_ocr_json', 's3_lookup', 'doc_alt_id', 'batch_id', 'doc_type', 'page_stats', 'public_uuid', 'bool_exception', 'bool_manual', 'doc_page_count', 'prev_page_image_web', 'next_page_image_web', 'next_next_page_image_web', 'prev_page_image_lookup', 'next_page_image_lookup', 'next_next_page_image_lookup', 'zooniverse_subject']


class DeedImageInline1st(admin.TabularInline):
    model = DeedPage
    verbose_name_plural = 'Deed page 1'
    fk_name = 'zooniverse_subject_1st_page'
    extra = 0
    exclude = deed_page_exclude_fields + ['zooniverse_subject_2nd_page', 'zooniverse_subject_3rd_page']
    # show_change_link = True

    readonly_fields = ['doc_num', 'book_id', 'page_num', 'split_page_num',
                       'doc_date', 'bool_match', 'matched_terms', 'page_ocr_text']
    
    def get_queryset(self, request):
        qs = super(DeedImageInline1st, self).get_queryset(request)
        return qs.only(*self.readonly_fields)

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class DeedImageInline2nd(DeedImageInline1st):
    verbose_name_plural = 'Deed page 2'
    fk_name = 'zooniverse_subject_2nd_page'
    exclude = deed_page_exclude_fields + ['zooniverse_subject_1st_page', 'zooniverse_subject_3rd_page']

    def get_queryset(self, request):
        qs = super(DeedImageInline2nd, self).get_queryset(request)
        return qs.only(*self.readonly_fields)


class DeedImageInline3rd(DeedImageInline1st):
    verbose_name_plural = 'Deed page 3'
    fk_name = 'zooniverse_subject_3rd_page'
    exclude = deed_page_exclude_fields + ['zooniverse_subject_1st_page', 'zooniverse_subject_2nd_page']


    def get_queryset(self, request):
        qs = super(DeedImageInline3rd, self).get_queryset(request)
        return qs.only(*self.readonly_fields)


class ManualSupportingDocumentInline(admin.StackedInline):
    model = ManualSupportingDocument
    extra = 0
    exclude = ['workflow']

# class ParcelInline(admin.TabularInline):
#     model = Parcel
#     extra = 0
#     exclude = ['orig_data']
#     # readonly_fields = ['doc_num', 'page_num',
#     # 'doc_date', 'bool_match', 'thumbnail_preview']


class ManualCorrectionInline(admin.StackedInline):
    model = ManualCorrection
    extra = 0
    exclude = ['workflow', 'zoon_subject_id', 'zoon_workflow_id']


class ExtraParcelCandidateInline(admin.StackedInline):
    model = ExtraParcelCandidate
    extra = 0
    exclude = ['workflow', 'zoon_subject_id', 'zoon_workflow_id']


class ManualParcelPINLinkInline(admin.StackedInline):
    model = ManualParcelPINLink
    extra = 0
    exclude = ['workflow', 'zoon_subject_id', 'zoon_workflow_id']


class ManualCovenantParcelPINLinkInline(admin.StackedInline):
    model = ManualCovenantParcelPINLink
    extra = 0
    exclude = ['workflow']


class ResponseInline(admin.TabularInline):
    model = ZooniverseResponseProcessed
    verbose_name = "Zooniverse individual response"
    verbose_name_plural = "Zooniverse individual response"
    extra = 0
    exclude = ['zoon_subject_id', 'classification_id', 'response_raw',
               'workflow', 'user_id', 'created_at']

    readonly_fields = [
        'bool_covenant', 'covenant_text', 'addition',
        'lot', 'block', 'city', 'seller',
        'map_book', 'map_book_page',
        'buyer', 'deed_date_year', 'deed_date_month', 'deed_date_day', 'user_name', 'match_type', 'bool_handwritten'
    ]


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


@ admin.register(ManualCovenant)
class ManualCovenantAdmin(admin.ModelAdmin):
    search_fields = ['addition', 'covenant_text', 'doc_num', 'comments']

    list_display = ('__str__', 'bool_parcel_match', 'bool_confirmed', 'addition', 'block', 'lot', 'deed_date', 'cov_type', )

    # exclude = ['join_candidates']

    fields = [
        'workflow',
        'cov_type',
        'bool_confirmed',
        'bool_parcel_match',
        'covenant_text',
        'addition',
        'block',
        'lot',
        'city',
        'buyer',
        'seller',
        'deed_date',
        'doc_num',
        'comments',
        'parcel_matches',
        'join_strings'
    ]

    list_filter = (
        'workflow__workflow_name',
        'bool_parcel_match',
        'cov_type',
        ('deed_date', DateRangeFilter),
    )

    inlines = [
        ManualCovenantParcelPINLinkInline,
        ManualSupportingDocumentInline
    ]

    readonly_fields = [
        'parcel_matches',
        'bool_parcel_match',
        'join_strings',
    ]


@ admin.register(ZooniverseSubject)
class SubjectAdmin(admin.ModelAdmin):

    # def get_queryset(self, request):
    #     qs = super(SubjectAdmin, self).get_queryset(request)
    #     return qs.select_related('zooniverse_subject_1st_page__set')

    search_fields = ['zoon_subject_id',
                     'addition_final', 'covenant_text', 'covenant_text_final']

    list_display = ('__str__', 'bool_covenant_final', 'bool_parcel_match',
                    'bool_manual_correction', 'bool_handwritten_final',
                    'addition_final', 'block_final', 'lot_final', 'deed_date_final', 'match_type_final', )

    list_filter = (
        'workflow__workflow_name',
        'bool_covenant_final',
        'bool_parcel_match',
        'bool_manual_correction',
        'match_type_final',
        'bool_handwritten_final',
        ('deed_date_final', DateRangeFilter),
        ScoreRangeListFilter,
        AdditionScoreRangeListFilter,
        DateScoreRangeListFilter,
        )

    inlines = [
        ManualCorrectionInline,
        ExtraParcelCandidateInline,
        ManualParcelPINLinkInline,
        # DeedImageInline,
        DeedImageInline1st,
        DeedImageInline2nd,
        DeedImageInline3rd,
        ResponseInline
    ]

    fieldsets = (
        ('Final values', {
            'fields': (
                'get_permalink',
                'deedpage_s3_lookup',
                'bool_covenant_final',
                'bool_parcel_match',
                'bool_handwritten_final',
                'covenant_text_final',
                'match_type_final',
                'addition_final',
                'lot_final',
                'block_final',
                'city_final',
                'map_book_final',
                'map_book_page_final',
                'seller_final',
                'buyer_final',
                'deed_date_final',
                'join_strings',
                'bool_manual_correction'
            )
        }),
        ('Matching parcels', {
            'fields': (
                #'geom_union_4326',
                'get_parcel_match_count',
                'parcel_matches',
            )
        }),
        ('Zooniverse basics', {
            'fields': (
                'zoon_subject_id',
                ('bool_covenant', 'bool_covenant_score'),
                'dt_retired',
                'median_score',

                ('covenant_text', 'covenant_text_score'),
            )
        }),
        ('Zooniverse property fields', {
            'fields': (
                ('addition', 'addition_score'),
                ('block', 'block_score'),
                ('lot', 'lot_score'),
                ('city', 'city_score'),
            ),
        }),
        ('Zooniverse deed date', {
            'fields': (
                ('deed_date', 'deed_date_overall_score'),
                ('deed_date_year_score',
                 'deed_date_month_score', 'deed_date_day_score'),
            ),
        }),
    )

    readonly_fields = [
        'workflow',
        'get_permalink',
        'get_parcel_match_count',
        'parcel_matches',
        'bool_parcel_match',
        'geom_union_4326',
        'zoon_subject_id',
        'join_strings',
        'bool_manual_correction',
        'bool_covenant_final',
        'bool_handwritten_final',
        'covenant_text_final',
        'match_type_final',
        'addition_final',
        'lot_final',
        'block_final',
        'map_book_final',
        'map_book_page_final',
        'seller_final',
        'buyer_final',
        'deed_date_final',
        'dt_retired',
        'median_score',
        'bool_covenant',
        'bool_covenant_score',
        'covenant_text',
        'covenant_text_score',
        'addition',
        'addition_score',
        'block',
        'block_score',
        'lot',
        'lot_score',
        'city',
        'city_final',
        'city_score',
        'deed_date',
        'deed_date_overall_score',
        'deed_date_year_score',
        'deed_date_month_score',
        'deed_date_day_score',
        'deedpage_s3_lookup',
    ]

    def get_parcel_match_count(self, obj):
        return obj.parcel_matches.count()
    get_parcel_match_count.short_description = 'Parcel match count'

    def get_permalink(self, obj):
        try:
            abs_url = reverse('zoon_subject_lookup', kwargs={"zoon_subject_id": str(obj.zoon_subject_id)})
            # print('hello' + abs_url)
            return mark_safe(f'<a href="{abs_url}" target="_blank">{abs_url}</a>')
        except NoReverseMatch:
            return ''

    # If you would like to add a default range filter
    # method pattern "get_rangefilter_{field_name}_default"
    def get_rangefilter_deed_date_default(self, request):
        return (datetime.date(1900, 1, 1), datetime.date(1970, 12, 31))

    # If you would like to change a title range filter
    # method pattern "get_rangefilter_{field_name}_title"
    def get_rangefilter_deed_date_title(self, request, field_path):
        return 'Deed date'


admin.site.enable_nav_sidebar = False
