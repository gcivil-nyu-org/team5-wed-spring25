from django.urls import path
from . import views

urlpatterns = [
    path('nycmap/', views.nycmap_view, name='nycmap'),
]