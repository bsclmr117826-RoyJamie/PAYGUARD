from django import forms

from repos.selectors import repositories_for_user


class UploadForm(forms.Form):
    """Only the repository choice is a form field. Files are read from request.FILES by the view."""
    repository = forms.ModelChoiceField(queryset=None, empty_label="Choose a repository")

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["repository"].queryset = repositories_for_user(user)
