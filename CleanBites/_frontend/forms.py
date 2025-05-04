from django.forms import ModelForm, Textarea
from django import forms
from _api._restaurants.models import Comment


class Review(ModelForm):
    class Meta:
        model = Comment
        fields = ("title", "comment", "rating", "health_rating")
        widgets = {
            "comment": Textarea(attrs={"cols": 80, "rows": 8}),
        }


class DeactivateAccountForm(forms.Form):
    confirm = forms.BooleanField(label="I confirm I want to deactivate my account.")
