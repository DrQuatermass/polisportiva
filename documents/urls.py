from django.urls import path
from .views import DocumentDetailView, DocumentListView, document_download

urlpatterns = [
    path('', DocumentListView.as_view(), name='documents_list'),
    path('<slug:slug>/scarica/', document_download, name='document_download'),
    path('<slug:slug>/', DocumentDetailView.as_view(), name='document_detail'),
]
