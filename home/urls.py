from django.urls import path
from django.views.generic import TemplateView

from .views import CalendarioView, ChiSiamoView, CiclismoView, ContattiView, HomeView

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('chi-siamo/', ChiSiamoView.as_view(), name='chi_siamo'),
    path('calendario/', CalendarioView.as_view(), name='calendario'),
    path('ciclismo/', CiclismoView.as_view(), name='ciclismo'),
    path('contatti/', ContattiView.as_view(), name='contatti'),
    path(
        'privacy-policy/',
        TemplateView.as_view(template_name='home/privacy_policy.html'),
        name='privacy_policy',
    ),
    path(
        'cookie-policy/',
        TemplateView.as_view(template_name='home/cookie_policy.html'),
        name='cookie_policy',
    ),
]
