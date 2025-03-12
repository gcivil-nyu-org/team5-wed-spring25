from django.urls import path
from . import views

urlpatterns = [
    path('nycmap/', views.nycmap_view, name='nycmap'),
    path('home/', views.home_view, name='home'),
]
