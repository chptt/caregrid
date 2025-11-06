from django.urls import path
from .views import home, dashboard_stats,login_view


urlpatterns = [
    path('login/', login_view, name='login'),
    path('dashboard_stats/', dashboard_stats, name='dashboard_stats'),
]
