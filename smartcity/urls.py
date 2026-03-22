from django.contrib import admin
from django.urls import path
from complaints.views import (
    login_view,
    menu_view,
    gov_dashboard_view,
    report_view,
    summary_view,
    track_list_view,
    track_detail_view,
    officer_update_view,
    logout_view
)

from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),

    path('', login_view, name='home'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),

    path('menu/', menu_view, name='menu'),
    path('report/', report_view, name='report'),
    path('summary/', summary_view, name='summary'),

    path('track/', track_list_view, name='track_list'),
    path('track/<int:complaint_id>/', track_detail_view, name='track_detail'),

    path('gov-dashboard/', gov_dashboard_view, name='gov'),
    path('officer/update/<int:complaint_id>/', officer_update_view, name='officer_update'),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)