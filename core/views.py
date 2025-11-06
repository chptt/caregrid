from django.http import HttpResponse, JsonResponse
from core.models import Patient, Doctor, Appointment
from firewall.views import block_ip_auto, access_control
from core.ip_tracker import track_login_attempt
from rest_framework.response import Response
from rest_framework.decorators import api_view

@api_view(['GET'])
def login_view(request):
    return Response({"message": "Login view placeholder"})

def home(request):
    return HttpResponse("Welcome to CareGrid API 🚑")

def dashboard_stats(request):
    # 🔹 Step 1: Extract IP safely
    ip = request.META.get('HTTP_X_FORWARDED_FOR')
    if ip:
        ip = ip.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', 'unknown')

    # 🔹 Step 2: Track login attempts
    attempts = track_login_attempt(ip)

    # 🔹 Step 3: Check if IP is already blocked
    try:
        if access_control.functions.isBlocked(ip).call():
            return JsonResponse({"error": "Access denied. IP is blocked due to suspicious activity."}, status=403)
    except Exception as e:
        return JsonResponse({"error": f"Blockchain check failed: {str(e)}"}, status=500)

    # 🔹 Step 4: Auto-block if too many requests
    if attempts > 10:
        try:
            block_ip_auto(ip)
            # Optional: log blocked IPs to file or DB here
            return JsonResponse({"error": "IP blocked due to rapid access attempts"}, status=403)
        except Exception as e:
            return JsonResponse({"error": f"Failed to block IP: {str(e)}"}, status=500)

    # 🔹 Step 5: Authenticated user check
    user = request.user
    if not user.is_authenticated:
        return JsonResponse({"error": "Unauthorized"}, status=401)

    # 🔹 Step 6: Branch check
    branch = getattr(user, 'branch', None)
    if not branch:
        return JsonResponse({"error": "No branch assigned"}, status=400)

    # 🔹 Step 7: Return dashboard stats
    data = {
        "patients": Patient.objects.filter(branch=branch).count(),
        "appointments": Appointment.objects.filter(branch=branch).count(),
        "doctors": Doctor.objects.filter(branch=branch).count(),
    }
    return JsonResponse(data)