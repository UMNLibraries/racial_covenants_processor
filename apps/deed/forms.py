from django import forms

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
        choices=[("", "All workflows")],  # you can populate dynamically later
    )

    bool_match = forms.BooleanField(
        label="Matches only?",
        required=False,
    )
