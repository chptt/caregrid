from django.urls import path
from . import views
from . import dashboard_views

urlpatterns = [
    # Legacy firewall endpoints
    path("block/", views.block_ip),
    path("check/", views.is_blocked),
    path("unblock/", views.unblock_ip),
    
    # Security dashboard endpoints
    path("security/dashboard/", dashboard_views.security_dashboard, name="security_dashboard"),
    path("security/stats/", dashboard_views.security_stats, name="security_stats"),
    path("security/block/", dashboard_views.admin_block_ip, name="admin_block_ip"),
    path("security/unblock/", dashboard_views.admin_unblock_ip, name="admin_unblock_ip"),
    path("security/blocked/", dashboard_views.blocked_ips_list, name="blocked_ips_list"),
]