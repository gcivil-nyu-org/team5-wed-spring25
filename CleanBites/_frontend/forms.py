from django.forms import ModelForm, Textarea
from _api._restaurants.models import Comment


class Review(ModelForm):
    class Meta:
        model = Comment
        fields = ('title', 'comment', 'rating', 'health_rating')
        widgets = {
            'comment' : Textarea(attrs={'cols': 80, 'rows': 8}),
        }