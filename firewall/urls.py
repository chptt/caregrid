from django.urls import path
from . import views

urlpatterns = [
    path("block/", views.block_ip),
    path("check/", views.is_blocked),
    path("unblock/", views.unblock_ip),
]