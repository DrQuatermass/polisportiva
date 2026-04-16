from django.urls import path
from .views import SponsorListView

urlpatterns = [
    path('', SponsorListView.as_view(), name='sponsors_list'),
]
