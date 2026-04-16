from django.urls import path
from .views import TeamDetailView, TeamListView

urlpatterns = [
    path('', TeamListView.as_view(), name='teams_list'),
    path('<slug:slug>/', TeamDetailView.as_view(), name='team_detail'),
]
