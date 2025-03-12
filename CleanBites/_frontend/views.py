from django.shortcuts import render


# Create your views here.
def nycmap_view(request):
    return render(request, "maps/nycmap.html")
