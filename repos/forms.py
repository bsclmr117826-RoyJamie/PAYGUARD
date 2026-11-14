from django import forms

from .models import Repository


class RepositoryForm(forms.ModelForm):
    url = forms.URLField(required=False, assume_scheme="https")

    class Meta:
        model = Repository
        fields = ["name", "url"]

    def __init__(self, *args, organization=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.organization = organization

    def clean_name(self):
        name = self.cleaned_data["name"].strip()
        if self.organization and Repository.objects.filter(organization=self.organization, name=name).exists():
            raise forms.ValidationError("Your organisation already has a repository with this name.")
        return name
