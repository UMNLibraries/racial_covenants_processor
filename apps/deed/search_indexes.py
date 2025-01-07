import datetime

from haystack import indexes

from apps.deed.models import DeedPage


class DeedPageIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    workflow = indexes.CharField(model_attr='workflow__workflow_name')
    doc_num = indexes.CharField(model_attr='doc_num', null=True)
    book_id = indexes.CharField(model_attr='book_id', null=True)
    page_num = indexes.CharField(model_attr='page_num', null=True)
    doc_date = indexes.DateTimeField(model_attr='doc_date', null=True)
    doc_type = indexes.CharField(model_attr='doc_type', null=True)
    bool_match = indexes.CharField(model_attr='bool_match')
    bool_exception = indexes.CharField(model_attr='bool_exception')
    matched_terms = indexes.MultiValueField()

    def get_model(self):
        return DeedPage

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.only(
            'workflow',
            's3_lookup',
            'doc_num',
            'doc_alt_id',
            'book_id',
            'page_num',
            'doc_date',
            'doc_type',
            'public_uuid',
            'bool_match',
            'bool_exception',
        ).prefetch_related('matched_terms').all()
    
    def prepare_matched_terms(self, obj):
        # Since we're using a M2M relationship with a complex lookup,
        # we can prepare the list here.
        return [term.term for term in obj.matched_terms.all()]