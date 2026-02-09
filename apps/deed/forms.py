from django import forms
from apps.zoon.models import ZooniverseWorkflow

class DeedSearchForm(forms.Form):
    q = forms.CharField(
        label="Search",
        required=False,
        widget=forms.TextInput(attrs={
            "placeholder": "Search deeds…"
        }),
    )

    workflow = forms.ChoiceField(
        label="Workflow filter",
        required=False,
        choices=[],  # Will be populated in __init__
    )

    bool_match = forms.BooleanField(
        label="Matches only?",
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Populate workflow choices from database
        workflows = ZooniverseWorkflow.objects.all().order_by('workflow_name')
        workflow_choices = [("", "All workflows")]
        workflow_choices.extend([(str(w.id), w.workflow_name) for w in workflows])
        self.fields['workflow'].choices = workflow_choices
