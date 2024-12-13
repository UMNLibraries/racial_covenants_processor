from django.shortcuts import render
from django import forms

from haystack.query import SearchQuerySet
from haystack.generic_views import SearchView
from haystack.forms import SearchForm

from apps.zoon.models import ZooniverseWorkflow


class DeedSearchForm(SearchForm):
    # bool_match = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class':'col-12-small'}))
    bool_match = forms.BooleanField(required=False)
    # end_date = forms.DateField(required=False)
    workflow = forms.ModelChoiceField(queryset=ZooniverseWorkflow.objects.all(), to_field_name="workflow_name", required=False)

    def search(self):
        # First, store the SearchQuerySet received from other processing.
        sqs = super().search()

        if not self.is_valid():
            return self.no_query_found()
        
        if self.cleaned_data['workflow']:
            sqs = sqs.filter(workflow=self.cleaned_data['workflow'])

        if self.cleaned_data['bool_match']:
            sqs = sqs.filter(bool_match=self.cleaned_data['bool_match'])

        return sqs


class DeedSearchView(SearchView):
    template_name = 'search/search.html'
    # queryset = SearchQuerySet().all()
    form_class = DeedSearchForm

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['all_workflows'] = ZooniverseWorkflow.objects.all()
        return data