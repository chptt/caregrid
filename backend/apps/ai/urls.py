from django.urls import path
from .api import views

app_name = 'ai'

urlpatterns = [
    path('doctor/chat', views.DoctorChatView.as_view(), name='doctor-chat'),
    path('medical-records/chat', views.MedicalRecordsChatView.as_view(), name='medical-records-chat'),
    path('upload-document', views.UploadDocumentView.as_view(), name='upload-document'),
    path('documents', views.DocumentListView.as_view(), name='document-list'),
    path('documents/<uuid:document_id>', views.DocumentDetailView.as_view(), name='document-detail'),
    path('conversations', views.ConversationListView.as_view(), name='conversation-list'),
    path('history/<uuid:conversation_id>', views.ConversationHistoryView.as_view(), name='conversation-history'),
]
