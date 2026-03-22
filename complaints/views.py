from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
import os
import uuid
from django.contrib.auth import logout
from django.contrib.auth import authenticate, login
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.cache import never_cache
from .ai_analysis import analyze_road_damage
from .models import Complaint, AIAnalysisResult


def logout_view(request):
    logout(request)
    return redirect("login")


@never_cache
def login_view(request):
    if request.method == "POST":
        role = request.POST.get("role")
        username = request.POST.get("email")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is None:
            return render(request, "complaints/page1.html", {
                "error": "Invalid email or password."
            })

        if role == "citizen":
            if user.is_staff or user.is_superuser:
                return render(request, "complaints/page1.html", {
                    "error": "This account is not allowed in Citizen portal."
                })

            login(request, user)
            return redirect("menu")

        elif role == "officer":
            if not (user.is_staff or user.is_superuser):
                return render(request, "complaints/page1.html", {
                    "error": "You are not authorized for SMC Officer portal."
                })

            login(request, user)
            return redirect("gov")

        return render(request, "complaints/page1.html", {
            "error": "Please select a valid role."
        })

    return render(request, "complaints/page1.html")

def logout_view(request):
    logout(request)
    return redirect("login")

def menu_view(request):
    return render(request, "complaints/page2.html")


def gov_dashboard_view(request):
    complaints = Complaint.objects.all().order_by("-created_at")

    total_count = complaints.count()
    pending_count = complaints.filter(status="pending").count()
    inprogress_count = complaints.filter(status="in_progress").count()
    resolved_count = complaints.filter(status="resolved").count()

    context = {
        "complaints": complaints,
        "total_count": total_count,
        "pending_count": pending_count,
        "inprogress_count": inprogress_count,
        "resolved_count": resolved_count,
    }

    return render(request, "complaints/pagegv.html", context)

def report_view(request):
    if request.method == "POST":
        image_file = request.FILES.get("image")

        if not image_file:
            return render(
                request,
                "complaints/page3.html",
                {"error": "Please upload an image of the road/pothole."},
            )

        # Save uploaded image to media/uploads/
        upload_dir = os.path.join(settings.MEDIA_ROOT, "uploads")
        os.makedirs(upload_dir, exist_ok=True)

        orig_ext = os.path.splitext(image_file.name)[1]
        unique_name = f"{uuid.uuid4().hex}{orig_ext}"
        saved_path = os.path.join(upload_dir, unique_name)

        with open(saved_path, "wb+") as dest:
            for chunk in image_file.chunks():
                dest.write(chunk)

        # Run AI
        analysis = analyze_road_damage(saved_path)

        image_url = settings.MEDIA_URL + "uploads/" + unique_name

        # Map form fields -> Complaint fields
        address = request.POST.get("address", "")
        landmark = request.POST.get("landmark", "")
        pincode = request.POST.get("pincode", "")
        description = request.POST.get("description", "")

        location = address
        if landmark:
            location += f", near {landmark}"
        if pincode:
            location += f" - {pincode}"

        # Create Complaint in DB
        complaint = Complaint.objects.create(
            user=request.user,
            title="Road Damage Complaint",
            description=description if description else "No description provided",
            category="road",
            location=location,
            status="pending",
            progress=10,
            image=f"uploads/{unique_name}",
        )

        # Save AI result in DB
        AIAnalysisResult.objects.create(
            complaint=complaint,
            detected_objects=analysis.get("all_labels", []),
            severity=analysis.get("severity", "low"),
            confidence=float(analysis.get("primary_confidence", 0)),
            ai_summary=analysis.get("summary", ""),
        )

        # Render page4 using DB complaint id
        context = {
            "complaint_id": complaint.id,
            "image_url": image_url,

            "primary_label": analysis.get("primary_label", ""),
            "severity": analysis.get("severity", ""),
            "confidence": analysis.get("primary_confidence", 0),
            "area_pixels": analysis.get("area_pixels", 0),
            "summary": analysis.get("summary", ""),
            "all_labels": analysis.get("all_labels", []),

            "name": request.POST.get("name", ""),
            "address": address,
            "landmark": landmark,
            "pincode": pincode,
            "phone": request.POST.get("phone", ""),
            "email": request.POST.get("email", ""),
            "description": description,
        }

        return render(request, "complaints/page4.html", context)

    return render(request, "complaints/page3.html")


def summary_view(request):
    if request.method == "POST":
        context = {
            "complaint_id": request.POST.get("complaint_id", ""),
            "image_url": request.POST.get("image_url", ""),
            "primary_label": request.POST.get("primary_label", ""),
            "severity": request.POST.get("severity", ""),
            "confidence": request.POST.get("confidence", ""),
            "area_pixels": request.POST.get("area_pixels", ""),
            "summary": request.POST.get("summary", ""),
            "name": request.POST.get("name", ""),
            "address": request.POST.get("address", ""),
            "landmark": request.POST.get("landmark", ""),
            "pincode": request.POST.get("pincode", ""),
            "phone": request.POST.get("phone", ""),
            "email": request.POST.get("email", ""),
            "description": request.POST.get("description", ""),
        }
        return render(request, "complaints/page5.html", context)

    return redirect("menu")


def track_list_view(request):
    """
    PageA: Citizen sees list of their complaints
    """
    complaints = Complaint.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "complaints/pageA.html", {"complaints": complaints})


def track_detail_view(request, complaint_id):
    """
    PageB: Citizen sees one complaint details + AI result + status/progress
    """
    complaint = get_object_or_404(Complaint, id=complaint_id, user=request.user)

    ai_result = None
    try:
        ai_result = complaint.ai_result
    except AIAnalysisResult.DoesNotExist:
        ai_result = None

    return render(
        request,
        "complaints/pageB.html",
        {"complaint": complaint, "ai_result": ai_result}
    )


def officer_update_view(request, complaint_id):
    """
    Officer updates complaint status and progress
    """
    complaint = get_object_or_404(Complaint, id=complaint_id)

    if request.method == "POST":
        new_status = request.POST.get("status")
        new_progress = request.POST.get("progress")

        if new_status in ["pending", "in_progress", "resolved"]:
            complaint.status = new_status

        try:
            progress_int = int(new_progress)
            complaint.progress = max(0, min(100, progress_int))
        except (TypeError, ValueError):
            pass

        complaint.save()

    return redirect("gov")