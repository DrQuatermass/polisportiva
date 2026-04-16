from django.urls import path
from .views import CalendarioView, ChiSiamoView, CiclismoView, ContattiView, HomeView

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('chi-siamo/', ChiSiamoView.as_view(), name='chi_siamo'),
    path('calendario/', CalendarioView.as_view(), name='calendario'),
    path('ciclismo/', CiclismoView.as_view(), name='ciclismo'),
    path('contatti/', ContattiView.as_view(), name='contatti'),
]
