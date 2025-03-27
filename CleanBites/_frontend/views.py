from django.shortcuts import get_object_or_404, render, redirect
from _api._restaurants.models import Restaurant
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from _api._users.models import Customer
from django.db import transaction

User = get_user_model()


# =====================================================================================
# WEBSITE VIEWS - visual endpoints
# =====================================================================================
def landing_view(request):
    return render(request, "landing.html")


@login_required(login_url="/login/")
def home_view(request):
    return render(request, "home.html")


@login_required(login_url="/login/")
def restaurant_detail(request, name):
    restaurant = get_object_or_404(Restaurant, name__iexact=name)
    return render(request, "maps/restaurant_detail.html", {"restaurant": restaurant})


@login_required(login_url="/login/")
def dynamic_map_view(request):
    return render(request, "maps/nycmap_dynamic.html")


@login_required(login_url="/login/")
def user_profile(request, username):
    user = get_object_or_404(Customer, username__iexact=username)
    return render(request, "user_profile.html", {"user": user})


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
        customer = Customer.objects.create(email=email, username=username)

        # ✅ Explicitly set authentication backend to avoid 'backend' error
        user.backend = "django.contrib.auth.backends.ModelBackend"

        # ✅ Log in the user
        login(request, user)

        return redirect("home")  # Redirect to homepage after registration

    return redirect("/")


def restaurant_register(request):
    restaurants = Restaurant.objects.filter(email="Not Provided").order_by("name")
    return render(request, "restaurant_register.html", {"restaurants": restaurants})


HARDCODE_VERIFY = "1234"


def restaurant_verify(request):
    if request.method == "POST":
        restaurant_id = request.POST.get("restaurant")  # Get selected restaurant ID
        username = request.POST.get("username").strip()
        email = request.POST.get("email").strip()
        password = request.POST.get("password").strip()
        confirm_password = request.POST.get("confirm_password").strip()
        verification_code = request.POST.get("verify").strip()

        # Check if passwords match
        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect("restaurant_register")

        # Check if the verification code is correct
        if verification_code != HARDCODE_VERIFY:
            messages.error(request, "Invalid verification code.")
            return redirect("restaurant_register")

        # Ensure username & email are unique
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username is already taken.")
            return redirect("restaurant_register")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email is already registered.")
            return redirect("restaurant_register")

        # Perform atomic transaction (user creation + restaurant email update)
        try:
            with transaction.atomic():
                # Create a new user in Django's auth_user table
                user = User.objects.create_user(
                    username=username, email=email, password=password
                )
                user.is_staff = False  # Optionally give them staff privileges
                user.save()

                # Update the selected restaurant's email
                restaurant = Restaurant.objects.get(id=restaurant_id)
                restaurant.email = email  # Assign new owner's email to restaurant
                restaurant.save()

            messages.success(request, "Registration successful! You can now log in.")
            return redirect("/")  # ✅ Redirect to landing page

        except Restaurant.DoesNotExist:
            messages.error(request, "Selected restaurant does not exist.")
            return redirect("restaurant_register")

        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect("restaurant_register")

    return redirect("restaurant_register")  # Redirect if accessed via GET
