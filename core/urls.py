from django.urls import path
from .views import home, dashboard_stats, login_view, rate_limit_status, test_rate_limit
from . import captcha_views
from . import patient_views
from . import appointment_views


urlpatterns = [
    path('login/', login_view, name='login'),
    path('dashboard_stats/', dashboard_stats, name='dashboard_stats'),
    
    # Rate limiting endpoints
    path('rate-limit/status/', rate_limit_status, name='rate_limit_status'),
    path('rate-limit/test/', test_rate_limit, name='test_rate_limit'),
    
    # CAPTCHA API endpoints
    path('security/captcha/', captcha_views.CaptchaView.as_view(), name='captcha'),
    path('security/captcha/status/', captcha_views.captcha_status, name='captcha_status'),
    
    # Patient management endpoints
    path('patients/', patient_views.register_patient, name='register_patient'),
    path('patients/search/', patient_views.search_patients, name='search_patients'),
    path('patients/<str:patient_id>/', patient_views.get_patient, name='get_patient'),
    path('branches/', patient_views.get_branches, name='get_branches'),
    
    # Appointment management endpoints
    path('appointments/', appointment_views.create_appointment, name='create_appointment'),
    path('appointments/list/', appointment_views.list_appointments, name='list_appointments'),
    path('appointments/<int:appointment_id>/', appointment_views.get_appointment, name='get_appointment'),
    path('appointments/patient/<str:patient_id>/', appointment_views.get_patient_appointments, name='get_patient_appointments'),
    path('doctors/', appointment_views.get_doctors, name='get_doctors'),
]
