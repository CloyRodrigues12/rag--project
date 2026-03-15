from django.urls import path
from .views import IngestURLView, ChatQueryView

urlpatterns = [
    path('ingest/', IngestURLView.as_view(), name='ingest_url'),
    path('chat/', ChatQueryView.as_view(), name='chat_query'),
]