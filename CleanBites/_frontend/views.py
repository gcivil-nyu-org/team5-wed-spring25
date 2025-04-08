from django.shortcuts import get_object_or_404, render, redirect
from _api._restaurants.models import Restaurant, Comment
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from _api._users.models import Customer, DM
from django.db.models import Q
from django.db import transaction
from django.http import HttpResponse
from _frontend.utils import has_unread_messages
from .forms import Review

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
def restaurant_detail(request, name):
    restaurant = get_object_or_404(Restaurant, name__iexact=name)
    reviews = Comment.objects.filter(restaurant=restaurant).order_by('-posted_at')
    is_owner = False
    if request.user.is_authenticated and request.user.username == restaurant.username:
        is_owner = True

    return render(
        request,
        "maps/restaurant_detail.html",
        {
            "restaurant": restaurant,
            "reviews" : reviews,
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
    user = get_object_or_404(Customer, username__iexact=username)
    context = {"user": user, "has_unread_messages": has_unread_messages(request.user)}
    return render(request, "user_profile.html", context)


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
def delete_conversation(request, other_user_id):
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
        restaurant = Restaurant.objects.get(user=request.user)
    except Restaurant.DoesNotExist:
        messages.error(request, "No restaurant is linked to your account.")
        return redirect("home")

    if request.method == "POST":
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
        else:
            restaurant.name = request.POST.get("name", restaurant.name)
            restaurant.building = request.POST.get("building", restaurant.building)
            restaurant.street = request.POST.get("street", restaurant.street)
            restaurant.zipcode = request.POST.get("zipcode", restaurant.zipcode)
            restaurant.phone = request.POST.get("phone", restaurant.phone)
            restaurant.cuisine_description = request.POST.get(
                "cuisine_description", restaurant.cuisine_description
            )
            restaurant.violation_description = request.POST.get(
                "description", restaurant.violation_description
            )

        if "profile_image" in request.FILES:
            restaurant.profile_image = request.FILES["profile_image"]

        restaurant.save()
        messages.success(request, "Restaurant profile updated successfully!")
        return redirect("restaurant_detail", name=restaurant.name)

    return redirect("home")


@login_required(login_url="/login/")
def profile_router(request, username):
    try:
        user_obj = Restaurant.objects.get(username=username)

        is_owner = False
        if request.user.is_authenticated and request.user.username == user_obj.username:
            is_owner = True
        reviews = Comment.objects.filter(restaurant=user_obj.name).order_by('-posted_at') #adding reviews 
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
            reviews = Comment.objects.filter(commenter=user_obj).order_by('-posted_at')
            return render(
                request,
                "user_profile.html",
                {
                    "customer": user_obj,
                    "reviews": reviews,
                    "has_unread_messages": has_unread_messages(request.user),
                },
            )
        except Customer.DoesNotExist:
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
            }

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
        },
    )


@login_required(login_url="/login/")
def send_message(request, chat_user_id):
    if request.method == "POST":
        sender = Customer.objects.get(email=request.user.email)
        recipient = get_object_or_404(Customer, id=chat_user_id)
        message_text = request.POST.get("message")

        if recipient == sender:
            messages.error(request, "You can't message yourself.")
            return redirect("chat", chat_user_id=recipient.id)

        if not message_text.strip():
            messages.error(request, "Message cannot be empty.")
            return redirect("chat", chat_user_id=recipient.id)

        # Save the DM
        DM.objects.create(
            sender=sender, receiver=recipient, message=message_text.encode("utf-8")
        )

        return redirect("chat", chat_user_id=recipient.id)
    

@login_required(login_url="/login/")
def send_message_generic(request):
    if request.method == "POST":
        sender = Customer.objects.get(email=request.user.email)
        recipient_email = request.POST.get("recipient")
        message_text = request.POST.get("message")

        try:
            recipient = Customer.objects.get(email=recipient_email)
            if recipient == sender:
                messages.error(request, "You can't message yourself.")
                return redirect("messages inbox")

            # Create DM
            DM.objects.create(
                sender=sender, receiver=recipient, message=message_text.encode("utf-8")
            )
            return redirect("chat", chat_user_id=recipient.id)

        except Customer.DoesNotExist:
            messages.error(request, "Recipient not found.")
            return redirect("messages inbox")


@login_required(login_url="/login/")
def delete_conversation(request, chat_user_id):
    try:
        user = Customer.objects.get(email=request.user.email)
        other_user = get_object_or_404(Customer, id=chat_user_id)

        # Delete all DMs between the two users
        DM.objects.filter(
            (Q(sender=user) & Q(receiver=other_user))
            | (Q(sender=other_user) & Q(receiver=user))
        ).delete()

        messages.success(
            request, f"Conversation with {other_user.first_name} has been deleted."
        )
    except Customer.DoesNotExist:
        messages.error(request, "User not found or you are not authorized.")

    return redirect("messages inbox")

@login_required(login_url="/login/")
def write_comment(request, id):
    restaurant_obj = get_object_or_404(Restaurant, id=id)
    author = get_object_or_404(Customer, username=request.user.username)

    if request.method == 'POST':
        form = Review(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.commenter = author
            review.restaurant = restaurant_obj
            review.rating = request.POST.get('rating')
            review.health_rating = request.POST.get('health_rating')
            review.save()
            return redirect('restaurant_detail', name=restaurant_obj.name)
        else:
            print(form.errors)  # helpful for debugging
    else:
        form = Review()

    context = {
        'restaurant': restaurant_obj,
        'form': form
    }
    return render(request, 'addreview.html', context)

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