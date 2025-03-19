from django.shortcuts import get_object_or_404, render, redirect
from _api._restaurants.models import Restaurant
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from _api._users.models import Customer

User = get_user_model()


# =====================================================================================
# WEBSITE VIEWS - visual endpoints
# =====================================================================================
def landing_view(request):
    return render(request, "landing.html")


@login_required(login_url="/login/")
def nycmap_view(request):
    return render(request, "maps/nycmap.html")


@login_required(login_url="/login/")
def home_view(request):
    return render(request, "home.html")


@login_required(login_url="/login/")
def restaurant_detail(request, name):
    restaurant = get_object_or_404(Restaurant, name__iexact=name)
    return render(request, "maps/restaurant_detail.html", {"restaurant": restaurant})


# =====================================================================================
# AUTHENTICATION VIEWS - doesn't return anything but authentication data
# =====================================================================================
def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect("home")  # Redirect to homepage after login
        else:
            messages.error(request, "Invalid username or password")
            return redirect("/")  # Stay on landing page

    return redirect("/")


def logout_view(request):
    logout(request)
    return redirect("/")


def register_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")

        if password1 != password2:
            messages.error(request, "Passwords do not match")
            return redirect("register")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken")
            return redirect("register")

        # Ensure email is unique in both User and Customer tables
        if (
            User.objects.filter(email=email).exists()
            or Customer.objects.filter(email=email).exists()
        ):
            messages.error(request, "Email is already in use")
            return redirect("register")

        # Create the user & customer
        user = User.objects.create_user(
            username=username, email=email, password=password1
        )
        customer = Customer.objects.create(email=email)

        # ✅ Explicitly set authentication backend to avoid 'backend' error
        user.backend = "django.contrib.auth.backends.ModelBackend"

        # ✅ Log in the user
        login(request, user)

        return redirect("home")  # Redirect to homepage after registration

    return redirect("/")
