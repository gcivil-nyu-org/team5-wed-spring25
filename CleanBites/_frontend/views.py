from django.shortcuts import get_object_or_404, render
from .models import Restaurant


# Create your views here.
def nycmap_view(request):
    return render(request, "maps/nycmap.html")


def restaurant_detail(request, restaurant_id):
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    return render(request, "maps/restaurant_detail.html", {"restaurant": restaurant})
