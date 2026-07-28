from django.urls import path
from caregrid.apps.ai.api import views

app_name = 'ai'

urlpatterns = [
    # Doctor Assistant
    path('doctor/chat/', views.DoctorChatView.as_view(), name='doctor-chat'),
    path('doctor/summarize/', views.DoctorSummarizeHistoryView.as_view(), name='doctor-summarize'),
    path('doctor/visit-summary/', views.DoctorVisitSummaryView.as_view(), name='doctor-visit-summary'),

    # Patient Assistant
    path('patient/chat/', views.PatientChatView.as_view(), name='patient-chat'),
    path('patient/explain-diagnosis/', views.PatientExplainDiagnosisView.as_view(), name='patient-explain'),
    path('patient/medication-info/', views.PatientMedicationInfoView.as_view(), name='patient-medication'),
    path('patient/general-health/', views.PatientGeneralHealthView.as_view(), name='patient-health'),

    # Medical Records Agent
    path('records/upload/', views.UploadDocumentView.as_view(), name='records-upload'),
    path('records/process/', views.ProcessDocumentView.as_view(), name='records-process'),

    # Summaries
    path('summaries/<uuid:summary_id>/approve/', views.ApproveSummaryView.as_view(), name='approve-summary'),

    # Conversations
    path('conversations/<uuid:conversation_id>/', views.ConversationHistoryView.as_view(), name='conversation-history'),

    # RAG / Knowledge Base
    path('rag/search/', views.RAGSearchView.as_view(), name='rag-search'),
    path('knowledge/', views.KnowledgeListView.as_view(), name='knowledge-list'),
]
