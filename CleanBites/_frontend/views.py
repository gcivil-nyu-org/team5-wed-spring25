from django.shortcuts import get_object_or_404, render, redirect
from _api._restaurants.models import Restaurant, Comment
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from _api._users.models import Customer, DM, FavoriteRestaurant, Moderator
from django.db.models import Q
from django.db import transaction
from django.http import HttpResponse
from _frontend.utils import has_unread_messages
from .forms import Review
from django.http import JsonResponse
from django.db.models import Avg
import json
from django.views.decorators.csrf import csrf_exempt, csrf_protect

# Get user model
User = get_user_model()

# Constants for message categories
AUTH_MESSAGE = "auth_message"  # For login/registration related messages
INBOX_MESSAGE = "inbox_message"  # For inbox related messages


# =====================================================================================
# WEBSITE VIEWS - visual endpoints
# =====================================================================================
def landing_view(request):
    return render(request, "landing.html")


@login_required(login_url="/login/")
def home_view(request):
    context = {"has_unread_messages": has_unread_messages(request.user)}
    return render(request, "home.html", context)


@login_required(login_url="/login/")
def restaurant_detail(request, id):
    restaurant = get_object_or_404(Restaurant, id=id)
    reviews = Comment.objects.filter(restaurant=restaurant).order_by("-posted_at")
    avg_rating = reviews.aggregate(Avg("rating"))["rating__avg"]
    avg_health = reviews.aggregate(Avg("health_rating"))["health_rating__avg"]
    is_owner = False
    if request.user.is_authenticated and request.user.username == restaurant.username:
        is_owner = True

    return render(
        request,
        "maps/restaurant_detail.html",
        {
            "restaurant": restaurant,
            "reviews": reviews,
            "avg_rating": avg_rating or 0,
            "avg_health": avg_health or 0,
            "is_owner": is_owner,
            "has_unread_messages": has_unread_messages(request.user),
        },
    )


@login_required(login_url="/login/")
def dynamic_map_view(request):
    context = {"has_unread_messages": has_unread_messages(request.user)}
    return render(request, "maps/nycmap_dynamic.html", context)


@login_required(login_url="/login/")
def user_profile(request, username):
    user = get_object_or_404(User, username=username)
    customer = None
    try:
        customer = Customer.objects.get(username=username)
    except Customer.DoesNotExist:
        customer = None

    is_owner = False
    if request.user.is_authenticated and request.user.username == user.username:
        is_owner = True

    if customer:
        reviews = Comment.objects.filter(commenter=customer.id).order_by("-posted_at")
    else:
        reviews = []

    context = {
        "profile_user": user,
        "has_unread_messages": has_unread_messages(request.user),
        "customer": customer,
        "is_owner": is_owner,
        "reviews": reviews,
    }
    return render(request, "user_profile.html", context)


@login_required(login_url="/login/")
def admin_profile(request, username):
    admin = get_object_or_404(Moderator, username__iexact=username)
    context = {"admin": admin}
    return render(request, "admin_profile.html", context)


@login_required(login_url="/login/")
def messages_view(request, chat_user_id=None):
    try:
        user = Customer.objects.get(email=request.user.email)
    except Customer.DoesNotExist:
        return render(
            request,
            "inbox.html",
            {
                "conversations": [],
                "active_chat": None,
                "messages": [],
                "error": "Your profile could not be found.",
                "has_unread_messages": has_unread_messages(request.user),
            },
        )

    all_dms = DM.objects.filter(Q(sender=user) | Q(receiver=user))

    participants = {}
    for dm in all_dms:
        other = dm.receiver if dm.sender == user else dm.sender
        if other.id not in participants:
            participants[other.id] = {
                "id": other.id,
                "name": other.first_name,
                "email": other.email,
                "avatar_url": "/static/images/avatar-placeholder.png",
                "has_unread": False,  # Initialize unread flag
            }

    # Check for unread messages in each conversation
    for participant_id in participants:
        has_unread = DM.objects.filter(
            sender_id=participant_id, receiver=user, read=False
        ).exists()
        participants[participant_id]["has_unread"] = has_unread

    conversations = list(participants.values())

    active_chat = None
    if chat_user_id:
        active_chat = get_object_or_404(Customer, id=chat_user_id)
    elif conversations:
        active_chat = get_object_or_404(Customer, id=conversations[0]["id"])

    messages = []
    if active_chat:
        raw_messages = DM.objects.filter(
            (Q(sender=user) & Q(receiver=active_chat))
            | (Q(sender=active_chat) & Q(receiver=user))
        ).order_by("sent_at")

        # Mark messages as read when viewed
        DM.objects.filter(sender=active_chat, receiver=user, read=False).update(
            read=True
        )

        for msg in raw_messages:
            try:
                byte_data = bytes(msg.message)
                msg.decoded_message = byte_data.decode("utf-8")
            except Exception as e:
                msg.decoded_message = "[Could not decode message]"
            messages.append(msg)

    return render(
        request,
        "inbox.html",
        {
            "conversations": conversations,
            "active_chat": active_chat,
            "messages": messages,
            "has_unread_messages": has_unread_messages(request.user),
        },
    )


@login_required(login_url="/login/")
def messages_view(request, chat_user_id=None):
    try:
        user = Customer.objects.get(email=request.user.email)
    except Customer.DoesNotExist:
        return render(
            request,
            "inbox.html",
            {
                "conversations": [],
                "active_chat": None,
                "messages": [],
                "error": "Your profile could not be found.",
                "has_unread_messages": has_unread_messages(request.user),
            },
        )

    all_dms = DM.objects.filter(Q(sender=user) | Q(receiver=user))

    participants = {}
    for dm in all_dms:
        other = dm.receiver if dm.sender == user else dm.sender
        if other.id not in participants:
            participants[other.id] = {
                "id": other.id,
                "name": other.first_name,
                "email": other.email,
                "avatar_url": "/static/images/avatar-placeholder.png",
                "has_unread": False,  # Initialize unread flag
            }

    # Check for unread messages in each conversation
    for participant_id in participants:
        has_unread = DM.objects.filter(
            sender_id=participant_id, receiver=user, read=False
        ).exists()
        participants[participant_id]["has_unread"] = has_unread

    conversations = list(participants.values())

    active_chat = None
    if chat_user_id:
        active_chat = get_object_or_404(Customer, id=chat_user_id)
    elif conversations:
        active_chat = get_object_or_404(Customer, id=conversations[0]["id"])

    messages = []
    if active_chat:
        raw_messages = DM.objects.filter(
            (Q(sender=user) & Q(receiver=active_chat))
            | (Q(sender=active_chat) & Q(receiver=user))
        ).order_by("sent_at")

        # Mark messages as read when viewed
        DM.objects.filter(sender=active_chat, receiver=user, read=False).update(
            read=True
        )

        for msg in raw_messages:
            try:
                byte_data = bytes(msg.message)
                msg.decoded_message = byte_data.decode("utf-8")
            except Exception as e:
                msg.decoded_message = "[Could not decode message]"
            messages.append(msg)

    return render(
        request,
        "inbox.html",
        {
            "conversations": conversations,
            "active_chat": active_chat,
            "messages": messages,
            "has_unread_messages": has_unread_messages(request.user),
        },
    )


@login_required(login_url="/login/")
def send_message(request, chat_user_id):
    if request.method == "POST":
        try:
            # Try to get sender from Customer
            sender = Customer.objects.get(email=request.user.email)
        except Customer.DoesNotExist:
            try:
                # If not found, try Restaurant
                sender = Restaurant.objects.get(email=request.user.email)
            except Restaurant.DoesNotExist:
                # Optional: handle case where sender is neither
                messages.error(
                    request,
                    "Your account was not found. Please contact support.",
                    extra_tags=INBOX_MESSAGE,
                )
                return HttpResponse("Sender not found", status=404)

        recipient = get_object_or_404(Customer, id=chat_user_id)
        message_text = request.POST.get("message")

        if recipient == sender:
            messages.error(
                request, "You can't message yourself.", extra_tags=INBOX_MESSAGE
            )
            return redirect("chat", chat_user_id=recipient.id)

        if not message_text.strip():
            messages.error(
                request, "Message cannot be empty.", extra_tags=INBOX_MESSAGE
            )
            return redirect("chat", chat_user_id=recipient.id)

        # Save the DM with read=False for new messages
        DM.objects.create(
            sender=sender,
            receiver=recipient,
            message=message_text.encode("utf-8"),
            read=False,
        )

        return redirect("chat", chat_user_id=recipient.id)


@login_required(login_url="/login/")
def send_message_generic(request):
    if request.method == "POST":
        try:
            # Try to get sender from Customer
            sender = Customer.objects.get(email=request.user.email)
        except Customer.DoesNotExist:
            try:
                # If not found, try Restaurant
                sender = Restaurant.objects.get(email=request.user.email)
            except Restaurant.DoesNotExist:
                # Optional: handle case where sender is neither
                messages.error(
                    request,
                    "Your account was not found. Please contact support.",
                    extra_tags=INBOX_MESSAGE,
                )
                return redirect("messages inbox")

        recipient_email = request.POST.get("recipient")
        message_text = request.POST.get("message")

        if not recipient_email:
            messages.error(
                request,
                "Please enter a recipient email address.",
                extra_tags=INBOX_MESSAGE,
            )
            return redirect("messages inbox")

        if not message_text.strip():
            messages.error(
                request, "Message cannot be empty.", extra_tags=INBOX_MESSAGE
            )
            return redirect("messages inbox")

        try:
            # First try to find the recipient as a Customer
            recipient = Customer.objects.get(email=recipient_email)

            if recipient == sender:
                messages.error(
                    request, "You can't message yourself.", extra_tags=INBOX_MESSAGE
                )
                return redirect("messages inbox")

            # Create DM with read=False for new messages
            DM.objects.create(
                sender=sender,
                receiver=recipient,
                message=message_text.encode("utf-8"),
                read=False,
            )

            return redirect("chat", chat_user_id=recipient.id)

        except Customer.DoesNotExist:
            # Check if recipient exists as a Restaurant
            try:
                restaurant_recipient = Restaurant.objects.get(email=recipient_email)
                messages.error(
                    request,
                    f"'{recipient_email}' is a restaurant account. Currently, you can only message customer accounts.",
                    extra_tags=INBOX_MESSAGE,
                )
            except Restaurant.DoesNotExist:
                # Recipient doesn't exist at all
                messages.error(
                    request,
                    f"Recipient '{recipient_email}' does not exist. Please check the email address and try again.",
                    extra_tags=INBOX_MESSAGE,
                )

            return redirect("messages inbox")


@login_required(login_url="/login/")
def delete_conversation(request, other_user_id, **kwargs):
    try:
        user = Customer.objects.get(email=request.user.email)
        other_user = Customer.objects.get(id=other_user_id)

        # Delete all messages between these two users (in both directions)
        DM.objects.filter(
            (Q(sender=user) & Q(receiver=other_user))
            | (Q(sender=other_user) & Q(receiver=user))
        ).delete()

        messages.success(
            request,
            f"Conversation with {other_user.first_name} has been deleted.",
            extra_tags=INBOX_MESSAGE,
        )
        return redirect("messages inbox")
    except Customer.DoesNotExist:
        messages.error(request, "Your account was not found.", extra_tags=INBOX_MESSAGE)
        return redirect("messages inbox")


@login_required(login_url="/login/")
def update_restaurant_profile_view(request):
    try:
        restaurant = Restaurant.objects.get(username=request.user)
    except Restaurant.DoesNotExist:
        messages.error(request, "No restaurant is linked to your account.")
        return redirect("home")

    if request.method == "POST":
        try:
            if "name" in request.POST:
                restaurant.name = request.POST.get("name")
            if "phone" in request.POST:
                restaurant.phone = request.POST.get("phone")
            if "street" in request.POST:
                restaurant.street = request.POST.get("street")
            if "building" in request.POST and request.POST.get("building").isdigit():
                restaurant.building = int(request.POST.get("building"))
            if "zipcode" in request.POST:
                restaurant.zipcode = request.POST.get("zipcode")
            if "cuisine_description" in request.POST:
                restaurant.cuisine_description = request.POST.get("cuisine_description")

            if "profile_image" in request.FILES:
                restaurant.profile_image = request.FILES["profile_image"]

            restaurant.save()
            messages.success(request, "Restaurant profile updated successfully!")
            return redirect("restaurant_detail", name=restaurant.id)
        except Exception as e:
            messages.error(request, f"Error updating profile: {e}")
            return redirect("home")

    return redirect("restaurant_detail", name=restaurant.id)


@login_required(login_url="/login/")
def profile_router(request, username):
    try:
        user_obj = Restaurant.objects.get(username=username)

        is_owner = False
        if request.user.is_authenticated and request.user.username == user_obj.username:
            is_owner = True
        reviews = Comment.objects.filter(restaurant=user_obj.id).order_by(
            "-posted_at"
        )  # adding reviews
        return render(
            request,
            "maps/restaurant_detail.html",
            {
                "restaurant": user_obj,
                "is_owner": is_owner,
                "reviews": reviews,
                "has_unread_messages": has_unread_messages(request.user),
            },
        )
    except Restaurant.DoesNotExist:
        try:
            user_obj = Customer.objects.get(username=username)
            profile_user = get_object_or_404(User, username=username)
            is_owner = False

            if (
                request.user.is_authenticated
                and request.user.username == user_obj.username
            ):
                is_owner = True

            reviews = Comment.objects.filter(commenter=user_obj.id).order_by(
                "-posted_at"
            )
            return render(
                request,
                "user_profile.html",
                {
                    "customer": user_obj,
                    "profile_user": profile_user,
                    "is_owner": is_owner,
                    "reviews": reviews,
                    "has_unread_messages": has_unread_messages(request.user),
                },
            )
        except Customer.DoesNotExist:
            try:
                admin_obj = Moderator.objects.get(username=username)
                return redirect("moderator_profile")
            except Moderator.DoesNotExist:
                return redirect("home")  # or a 404 page


@login_required(login_url="/login/")
def debug_unread_messages(request):
    """Debug view to check unread messages status."""
    from django.http import JsonResponse

    try:
        user = Customer.objects.get(email=request.user.email)
        unread_count = DM.objects.filter(receiver=user, read=False).count()
        unread_messages = list(
            DM.objects.filter(receiver=user, read=False).values(
                "id", "sender__email", "sent_at"
            )
        )

        # Format sent_at for better readability
        for msg in unread_messages:
            if "sent_at" in msg:
                msg["sent_at"] = msg["sent_at"].strftime("%Y-%m-%d %H:%M:%S")

        return JsonResponse(
            {
                "has_unread_messages": has_unread_messages(request.user),
                "unread_count": unread_count,
                "unread_messages": unread_messages,
                "user_email": request.user.email,
                "is_authenticated": request.user.is_authenticated,
            }
        )
    except Customer.DoesNotExist:
        return JsonResponse(
            {
                "error": "Customer not found",
                "user_email": request.user.email,
                "is_authenticated": request.user.is_authenticated,
            }
        )
    except Exception as e:
        return JsonResponse(
            {
                "error": str(e),
                "user_email": request.user.email,
                "is_authenticated": request.user.is_authenticated,
            }
        )


@login_required(login_url="/login/")
def write_comment(request, id):
    restaurant_obj = get_object_or_404(Restaurant, id=id)
    author = get_object_or_404(Customer, username=request.user.username)

    if request.method == "POST":
        form = Review(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.commenter = author
            review.restaurant = restaurant_obj
            review.rating = request.POST.get("rating")
            review.health_rating = request.POST.get("health_rating")
            review.save()
            return redirect("restaurant_detail", id=restaurant_obj.id)
        else:
            print(form.errors)  # helpful for debugging
    else:
        form = Review()

    context = {"restaurant": restaurant_obj, "form": form}
    return render(request, "addreview.html", context)


@login_required(login_url="/login/")
def moderator_profile_view(request):
    # verify user is a moderator
    try:
        moderator = Moderator.objects.get(email=request.user.email)
    except Moderator.DoesNotExist:
        messages.error(request, "Unauthorized action.")
        return redirect("home")
    # query for flagged DMs and comments
    flagged_dms = DM.objects.filter(flagged=True)
    flagged_comments = Comment.objects.filter(flagged=True)

    # decode DM messages
    for dm in flagged_dms:
        try:
            dm.decoded_message = bytes(dm.message).decode("utf-8")
        except Exception as e:
            dm.decoded_message = "[Could not decode message]"

    context = {
        "moderator": moderator,
        "flagged_dms": flagged_dms,
        "flagged_comments": flagged_comments,
    }
    return render(request, "admin_profile.html", context)


@login_required(login_url="/login/")
def deactivate_account(request, user_type, user_id):
    # verify user is a moderator
    try:
        moderator = Moderator.objects.get(email=request.user.email)
    except Moderator.DoesNotExist:
        messages.error(request, "Unauthorized action.")
        return redirect("home")

    if user_type == "customer":
        user_obj = get_object_or_404(Customer, id=user_id)
    elif user_type == "restaurant":
        user_obj = get_object_or_404(Restaurant, id=user_id)
    else:
        messages.error(request, "Invalid user type.")
        return redirect("moderator_profile")

    # # deactivate Django user instance
    # if hasattr(user_obj, "user"):
    #     user_obj.user.is_active = False
    #     user_obj.user.save()
    # else:
    #     user_obj.is_activated = False
    #     user_obj.save()
    user_obj.is_activated = False
    user_obj.save()

    messages.success(
        request, f"{user_type.capitalize()} account deactivated successfully."
    )
    return redirect("moderator_profile")


@login_required(login_url="/login/")
def delete_comment(request, comment_id):
    try:
        moderator = Moderator.objects.get(email=request.user.email)
    except Moderator.DoesNotExist:
        messages.error(request, "Unauthorized action.")
        return redirect("home")

    comment = get_object_or_404(Comment, id=comment_id)
    comment.delete()
    messages.success(request, "Comment deleted successfully.")
    return redirect("moderator_profile")


@login_required(login_url="/login/")
def global_search(request):
    query = request.GET.get("q", "").strip()
    if not query:
        return JsonResponse({"results": []})

    customers = Customer.objects.filter(username__icontains=query).values("username")[
        :5
    ]
    restaurants = Restaurant.objects.filter(name__icontains=query).values(
        "id", "name", "username"
    )[:5]

    results = []

    for c in customers:
        results.append(
            {"label": f"👤 {c['username']}", "url": f"/user/{c['username']}/"}
        )

    for r in restaurants:
        results.append({"label": f"🍽️ {r['name']}", "url": f"/restaurant/{r['id']}/"})

    return JsonResponse({"results": results})


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
            messages.error(
                request, "Invalid username or password", extra_tags=AUTH_MESSAGE
            )
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
            messages.error(request, "Passwords do not match", extra_tags=AUTH_MESSAGE)
            return redirect("register")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken", extra_tags=AUTH_MESSAGE)
            return redirect("register")

        # Ensure email is unique in both User and Customer tables
        if (
            User.objects.filter(email=email).exists()
            or Customer.objects.filter(email=email).exists()
        ):
            messages.error(request, "Email is already in use", extra_tags=AUTH_MESSAGE)
            return redirect("register")

        # Create the user & customer
        user = User.objects.create_user(
            username=username, email=email, password=password1
        )
        customer = Customer.objects.create(email=email, username=username)
        # Explicitly set authentication backend to avoid 'backend' error
        user.backend = "django.contrib.auth.backends.ModelBackend"

        # Log in the user
        login(request, user)

        return redirect("home")  # Redirect to homepage after registration

    return redirect("/")


def moderator_register(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")

        if password1 != password2:
            messages.error(request, "Passwords do not match", extra_tags=AUTH_MESSAGE)
            return redirect("register")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken", extra_tags=AUTH_MESSAGE)
            return redirect("register")

        # Ensure email is unique in both User and Moderator tables
        if (
            User.objects.filter(email=email).exists()
            or Moderator.objects.filter(email=email).exists()
        ):
            messages.error(request, "Email is already in use", extra_tags=AUTH_MESSAGE)
            return redirect("register")

        # Create the user & moderator
        user = User.objects.create_user(
            username=username, email=email, password=password1
        )
        moderator = Moderator.objects.create(email=email, username=username)

        # Explicitly set authentication backend to avoid 'backend' error
        user.backend = "django.contrib.auth.backends.ModelBackend"

        # Log in the user
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
            messages.error(request, "Passwords do not match.", extra_tags=AUTH_MESSAGE)
            return redirect("restaurant_register")

        # Check if the verification code is correct
        if verification_code != HARDCODE_VERIFY:
            messages.error(
                request, "Invalid verification code.", extra_tags=AUTH_MESSAGE
            )
            return redirect("restaurant_register")

        # Ensure username & email are unique
        if User.objects.filter(username=username).exists():
            messages.error(
                request, "Username is already taken.", extra_tags=AUTH_MESSAGE
            )
            return redirect("restaurant_register")

        if User.objects.filter(email=email).exists():
            messages.error(
                request, "Email is already registered.", extra_tags=AUTH_MESSAGE
            )
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
                restaurant.username = username
                restaurant.save()

            messages.success(
                request,
                "Registration successful! You can now log in.",
                extra_tags=AUTH_MESSAGE,
            )
            return redirect("/")  # Redirect to landing page

        except Restaurant.DoesNotExist:
            messages.error(
                request, "Selected restaurant does not exist.", extra_tags=AUTH_MESSAGE
            )
            return redirect("restaurant_register")

        except Exception as e:
            messages.error(
                request, f"An error occurred: {str(e)}", extra_tags=AUTH_MESSAGE
            )
            return redirect("restaurant_register")

    return redirect("restaurant_register")  # Redirect if accessed via GET


# =====================================================================================
# CSRF EXEMPT/PROTECTED VIEWS - need to update this later probably
# =====================================================================================


@csrf_exempt
@login_required(login_url="/login/")
def bookmarks_view(request):
    if request.method == "POST":
        try:
            restaurant_id = request.POST.get("restaurant_id")
            if not restaurant_id:
                return JsonResponse(
                    {"success": False, "error": "Restaurant ID required"}, status=400
                )

            restaurant = Restaurant.objects.get(id=restaurant_id)
            customer = Customer.objects.get(username=request.user.username)

            # Check if bookmark exists
            if FavoriteRestaurant.objects.filter(
                customer=customer, restaurant=restaurant
            ).exists():
                return JsonResponse(
                    {"success": False, "error": "Restaurant already bookmarked"},
                    status=400,
                )

            FavoriteRestaurant.objects.create(customer=customer, restaurant=restaurant)
            return JsonResponse(
                {"success": True, "message": "Bookmark added successfully"}
            )

        except Restaurant.DoesNotExist:
            return JsonResponse(
                {"success": False, "error": "Restaurant not found"}, status=404
            )
        except Customer.DoesNotExist:
            return JsonResponse(
                {"success": False, "error": "User not found"}, status=404
            )
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)

    if request.method == "DELETE":
        try:
            data = json.loads(request.body)
            bookmark_id = data.get("id")  # or "bookmark_id", just keep consistent

            if not bookmark_id:
                return JsonResponse(
                    {"success": False, "error": "Missing bookmark ID"}, status=400
                )

            customer = Customer.objects.get(username=request.user.username)

            # ✅ Delete by the bookmark's actual ID (primary key of FavoriteRestaurant)
            deleted, _ = FavoriteRestaurant.objects.filter(
                id=bookmark_id, customer=customer
            ).delete()

            if deleted:
                return JsonResponse({"success": True, "message": "Bookmark deleted"})
            else:
                return JsonResponse(
                    {"success": False, "error": "Bookmark not found"}, status=404
                )

        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)

    try:
        if not hasattr(request.user, "username"):
            return JsonResponse({"error": "Customer profile missing"}, status=400)

        customer = Customer.objects.get(username=request.user.username)

        # Get restaurant IDs from the user's bookmarks
        favorite_qs = FavoriteRestaurant.objects.filter(customer=customer)

        restaurant_ids = favorite_qs.values_list("restaurant_id", flat=True)

        # Original restaurant list (unchanged)
        restaurants = list(
            Restaurant.objects.filter(id__in=restaurant_ids).values(
                "id", "name", "phone", "cuisine_description"
            )
        )

        # New bookmarks list: bookmark ID + restaurant ID
        bookmarks = list(favorite_qs.values("id", "restaurant_id"))

        return JsonResponse(
            {
                "restaurants": restaurants,
                "bookmarks": bookmarks,
                "count": len(restaurants),
            }
        )
    except Exception as e:
        return JsonResponse({"error": str(e), "type": type(e).__name__}, status=500)


@csrf_protect
@login_required(login_url="/login/")
def update_profile(request):
    print("=== HIT update_profile ===")
    print("Authenticated:", request.user.is_authenticated)

    if not request.user.is_authenticated:
        return JsonResponse({"error": "Authentication required"}, status=401)

    if request.method != "POST":
        return JsonResponse({"error": "Invalid method"}, status=405)

    try:
        # Parse JSON body
        data = json.loads(request.body)

        name = data.get("name", "").strip()
        email = data.get("email", "").strip()
        aboutme = data.get("aboutme", "").strip()
        currentUser = data.get("currentUsername", "").strip()

        # Split full name into first and last
        parts = name.split(" ", 1)
        request.user.first_name = parts[0]
        request.user.last_name = parts[1] if len(parts) > 1 else ""
        request.user.email = email
        request.user.save()

        customer = Customer.objects.get(username=currentUser)
        customer.aboutme = aboutme
        customer.save()

        return JsonResponse(
            {
                "name": f"{request.user.first_name} {request.user.last_name}",
                "email": request.user.email,
                "aboutme": customer.aboutme,
            }
        )

    except Customer.DoesNotExist:
        return JsonResponse({"error": "Customer profile not found."}, status=404)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)
