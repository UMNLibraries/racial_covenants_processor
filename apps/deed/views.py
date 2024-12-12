from django.shortcuts import render
from django import forms

from haystack.query import SearchQuerySet
from haystack.generic_views import SearchView
from haystack.forms import SearchForm


class DeedSearchForm(SearchForm):
    bool_match = forms.BooleanField(required=False)
    # end_date = forms.DateField(required=False)

    def search(self):
        # First, store the SearchQuerySet received from other processing.
        sqs = super().search()

        if not self.is_valid():
            return self.no_query_found()

        if self.cleaned_data['bool_match']:
            sqs = sqs.filter(bool_match=self.cleaned_data['bool_match'])

        return sqs


class DeedSearchView(SearchView):
    template_name = 'search/search.html'
    # queryset = SearchQuerySet().all()
    form_class = DeedSearchForm
