import json
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import JsonResponse, HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from .models import User, Email

def index(request):
    if request.user.is_authenticated:
        return render(request, "mail/inbox.html")
    else:
        return HttpResponseRedirect(reverse("login"))

# ================= COMPOSE EMAIL (UPDATED) =================
@csrf_exempt
@login_required
def compose(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST request required."}, status=400)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON."}, status=400)

    recipients_raw = data.get("recipients", "")
    if not recipients_raw:
        return JsonResponse({"error": "At least one recipient required."}, status=400)

    emails = [email.strip() for email in recipients_raw.split(",")]
    recipients = []
    for email_addr in emails:
        try:
            user = User.objects.get(email=email_addr)
            recipients.append(user)
        except User.DoesNotExist:
            # Ippo intha user register aagi iruntha mattum thaan mail pogum
            return JsonResponse({"error": f"User with email {email_addr} does not exist. They must register first."}, status=400)

    subject = data.get("subject", "")
    body = data.get("body", "")

    # Save logic: Creating separate records for Sent and Inbox
    for recipient in recipients:
        # 1. Sender's copy (for 'Sent' folder)
        sent_email = Email(
            user=request.user,
            sender=request.user,
            subject=subject,
            body=body,
            read=True
        )
        sent_email.save()
        sent_email.recipients.add(recipient)
        
        # 2. Recipient's copy (for 'Inbox' folder)
        # Neenga ungalukkae anupuna, Sent box-layum Inbox-layum vara ippadi pannanum
        if recipient != request.user:
            inbox_email = Email(
                user=recipient,
                sender=request.user,
                subject=subject,
                body=body,
                read=False
            )
            inbox_email.save()
            inbox_email.recipients.add(recipient)
        else:
            # If sending to self, mark it to show in inbox too
            sent_email.recipients.add(request.user)

    return JsonResponse({"message": "Email sent successfully."}, status=201)

# ================= MAILBOX =================
@login_required
def mailbox(request, mailbox):
    if mailbox == "inbox":
        # Only show emails where the user IS the recipient
        emails = Email.objects.filter(
            user=request.user, recipients=request.user, archived=False
        )
    elif mailbox == "sent":
        # Only show emails where the user IS the sender
        emails = Email.objects.filter(
            user=request.user, sender=request.user
        )
    elif mailbox == "archive":
        emails = Email.objects.filter(
            user=request.user, recipients=request.user, archived=True
        )
    else:
        return JsonResponse({"error": "Invalid mailbox."}, status=400)

    emails = emails.order_by("-timestamp").all()
    return JsonResponse([email.serialize() for email in emails], safe=False)

# ================= SINGLE EMAIL =================
@csrf_exempt
@login_required
def email(request, email_id):
    try:
        email = Email.objects.get(user=request.user, pk=email_id)
    except Email.DoesNotExist:
        return JsonResponse({"error": "Email not found."}, status=404)

    if request.method == "GET":
        return JsonResponse(email.serialize())
    elif request.method == "PUT":
        data = json.loads(request.body)
        if data.get("read") is not None:
            email.read = data["read"]
        if data.get("archived") is not None:
            email.archived = data["archived"]
        email.save()
        return HttpResponse(status=204)
    else:
        return JsonResponse({"error": "GET or PUT request required."}, status=400)

# ================= AUTH FUNCTIONS =================
def login_view(request):
    if request.method == "POST":
        email = request.POST["email"]
        password = request.POST["password"]
        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "mail/login.html", {"message": "Invalid email and/or password."})
    return render(request, "mail/login.html")

def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))

def register(request):
    if request.method == "POST":
        email = request.POST["email"]
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "mail/register.html", {"message": "Passwords must match."})
        try:
            user = User.objects.create_user(email, email, password)
            user.save()
        except IntegrityError:
            return render(request, "mail/register.html", {"message": "Email address already taken."})
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    return render(request, "mail/register.html")