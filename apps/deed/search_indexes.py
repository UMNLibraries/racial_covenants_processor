import datetime

from haystack import indexes

from .models import DeedPage


class DeedPageIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    workflow = indexes.CharField(model_attr='workflow__workflow_name')
    doc_date = indexes.DateTimeField(model_attr='doc_date')
    doc_type = indexes.CharField(model_attr='doc_type')
    bool_match = indexes.CharField(model_attr='bool_match')
    bool_exception = indexes.CharField(model_attr='bool_exception')

    def get_model(self):
        return DeedPage

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.all()