from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    """
    Extends Django's built‑in User model with a role and optional details.
    Each user will have one profile telling us if they are a citizen or an SMC official.
    """

    ROLE_CHOICES = [
        ('citizen', 'Citizen'),
        ('official', 'SMC Official'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='citizen')
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user.username} ({self.role})"


class Complaint(models.Model):
    """
    One record per complaint submitted by a citizen.
    Stores basic info plus optional image/video and status.
    """

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
    ]

    CATEGORY_CHOICES = [
        ('road', 'Road Damage'),
        ('garbage', 'Garbage'),
        ('water', 'Water Supply'),
        ('electricity', 'Electricity'),
        ('other', 'Other'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='complaints')
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='other')

    # Media files
    image = models.ImageField(upload_to='complaints/images/', blank=True, null=True)
    video = models.FileField(upload_to='complaints/videos/', blank=True, null=True)

    # Location (you can later add lat/long if needed)
    location = models.CharField(max_length=255)

    # Workflow status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    progress = models.PositiveSmallIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"


class AIAnalysisResult(models.Model):
    """
    Stores the AI analysis output for a given complaint.
    There is typically one analysis record per complaint.
    """

    complaint = models.OneToOneField(
        Complaint,
        on_delete=models.CASCADE,
        related_name='ai_result'
    )

    # Objects / classes detected by your model (pothole, garbage, etc.)
    detected_objects = models.JSONField(default=list, blank=True)

    # Severity classification decided by your logic ("high", "medium", "low")
    severity = models.CharField(max_length=20)

    # Confidence score from your model (0.0 - 1.0 or 0 - 100)
    confidence = models.FloatField()

    # Human‑readable explanation
    ai_summary = models.TextField()

    # Optional: path to processed image (with bounding boxes drawn)
    processed_image = models.ImageField(
        upload_to='complaints/ai_processed/',
        blank=True,
        null=True
    )

    analyzed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"AI Result for: {self.complaint.title} – Severity: {self.severity}"