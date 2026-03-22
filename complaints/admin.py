from django.contrib import admin
from .models import UserProfile, Complaint, AIAnalysisResult

admin.site.register(UserProfile)
admin.site.register(Complaint)
admin.site.register(AIAnalysisResult)