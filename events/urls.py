from django.urls import path
from .views import (
    EventDetailView, EventListView,
    event_register, event_payment, event_registration_confirm,
    event_social_image, paypal_create_order, paypal_capture_order,
)

urlpatterns = [
    path('', EventListView.as_view(), name='events_list'),
    path('iscrizione/<uuid:registration_id>/', event_payment, name='event_payment'),
    path('conferma/<uuid:registration_id>/', event_registration_confirm, name='event_registration_confirm'),
    path('paypal/create/<uuid:registration_id>/', paypal_create_order, name='paypal_create_order'),
    path('paypal/capture/<uuid:registration_id>/', paypal_capture_order, name='paypal_capture_order'),
    path('<slug:slug>/social.jpg', event_social_image, name='event_social_image'),
    path('<slug:slug>/iscriviti/', event_register, name='event_register'),
    path('<slug:slug>/', EventDetailView.as_view(), name='event_detail'),
]
