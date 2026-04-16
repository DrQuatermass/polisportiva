from django.urls import path
from .views import DocumentDetailView, DocumentListView

urlpatterns = [
    path('', DocumentListView.as_view(), name='documents_list'),
    path('<slug:slug>/', DocumentDetailView.as_view(), name='document_detail'),
]
