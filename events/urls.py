from django.urls import path
from .views import (
    EventDetailView, EventListView,
    event_register, event_payment, event_registration_confirm,
    event_social_image, paypal_start, paypal_return,
)

urlpatterns = [
    path('', EventListView.as_view(), name='events_list'),
    path('iscrizione/<uuid:registration_id>/', event_payment, name='event_payment'),
    path('conferma/<uuid:registration_id>/', event_registration_confirm, name='event_registration_confirm'),
    path('paypal/start/<uuid:registration_id>/', paypal_start, name='paypal_start'),
    path('paypal/return/<uuid:registration_id>/', paypal_return, name='paypal_return'),
    path('<slug:slug>/og-image', event_social_image, name='event_social_image'),
    path('<slug:slug>/iscriviti/', event_register, name='event_register'),
    path('<slug:slug>/', EventDetailView.as_view(), name='event_detail'),
]
