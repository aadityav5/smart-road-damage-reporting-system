from django.urls import path
from .views import test_ai_view   # make sure test_ai_view exists in views.py

urlpatterns = [
    path('test-ai/', test_ai_view, name='test_ai'),
]