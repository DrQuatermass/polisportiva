import logging
import uuid

import requests
from django.conf import settings
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import DetailView, ListView

from config.social_images import social_image_response

from .forms import build_registration_form
from .models import Event, Registration, RegistrationAnswer

logger = logging.getLogger(__name__)


def _paypal_error_payload(resp):
    try:
        data = resp.json()
    except ValueError:
        data = {'message': resp.text}

    message = data.get('message') or data.get('name') or resp.reason
    details = data.get('details') or []
    if details:
        issues = [
            detail.get('description') or detail.get('issue')
            for detail in details
            if detail.get('description') or detail.get('issue')
        ]
        if issues:
            message = f'{message}: {"; ".join(issues)}'

    return {'error': message, 'paypal': data}


def _extract_capture_status(result):
    """Ritorna lo stato reale della cattura PayPal (COMPLETED/PENDING/DECLINED)
    letto da purchase_units[].payments.captures[]. Se non disponibile,
    ripiega sullo stato dell'ordine."""
    try:
        captures = result['purchase_units'][0]['payments']['captures']
        status = captures[0].get('status')
        if status:
            return status
    except (KeyError, IndexError, TypeError):
        pass
    return result.get('status')


def _extract_custom_id(result):
    """Ritorna il custom_id (= id iscrizione) dalla risposta PayPal, per
    verificare che l'ordine catturato appartenga davvero a questa iscrizione."""
    try:
        pu = result['purchase_units'][0]
    except (KeyError, IndexError, TypeError):
        return None
    if pu.get('custom_id'):
        return pu['custom_id']
    try:
        return pu['payments']['captures'][0].get('custom_id')
    except (KeyError, IndexError, TypeError):
        return None


def _send_confirmation_email(registration):
    event = registration.event
    status = registration.payment_status
    if status == 'completed':
        payment_note = 'Pagamento ricevuto.'
    elif status == 'review':
        payment_note = (
            'Abbiamo ricevuto il pagamento: è in fase di verifica da parte di PayPal. '
            'Ti confermeremo appena la verifica sarà completata.'
        )
    else:
        payment_note = ''

    subject = f'Conferma iscrizione: {event.title}'
    body = (
        f'Ciao,\n\n'
        f'la tua iscrizione all\'evento "{event.title}" è stata ricevuta con successo.\n'
    )
    if event.date:
        body += f'Data evento: {event.date.strftime("%d/%m/%Y %H:%M")}\n'
    if payment_note:
        body += f'{payment_note}\n'
    body += (
        f'\nNumero iscrizione: {registration.id}\n\n'
        f'Per qualsiasi informazione contattaci a {settings.CONTACT_EMAIL}.\n\n'
        f'Polisportiva Sanmarinese di Carpi'
    )

    try:
        send_mail(
            subject=subject,
            message=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[registration.email],
            fail_silently=False,
        )
    except Exception as e:
        logger.error('Errore invio email conferma iscrizione %s: %s', registration.id, e)


class EventListView(ListView):
    model = Event
    template_name = 'events/list.html'
    context_object_name = 'events'

    def get_queryset(self):
        return Event.objects.filter(published=True, date__gte=timezone.now())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['past_events'] = Event.objects.filter(published=True, date__lt=timezone.now())[:6]
        return context


class EventDetailView(DetailView):
    model = Event
    template_name = 'events/detail.html'
    context_object_name = 'event'
    slug_field = 'slug'

    def get_queryset(self):
        return Event.objects.filter(published=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event = self.object
        if event.registration_enabled:
            context['reg_form'] = build_registration_form(event)
            context['paypal_client_id'] = getattr(settings, 'PAYPAL_CLIENT_ID', '')
        return context


def event_social_image(request, slug):
    event = get_object_or_404(Event, slug=slug, published=True)
    return social_image_response(event.og_image or event.image)


def event_register(request, slug):
    event = get_object_or_404(Event, slug=slug, published=True)

    if not event.registrations_open:
        return render(request, 'events/registration_closed.html', {'event': event})

    if request.method == 'GET':
        return redirect('event_detail', slug=slug)

    form = build_registration_form(event, data=request.POST, files=request.FILES)
    if form.is_valid():
        email = form.cleaned_data['reg_email']
        status = 'pending' if event.is_paid else 'free'
        registration = Registration.objects.create(
            event=event,
            email=email,
            payment_status=status,
            amount_paid=event.registration_price,
        )
        for rf in event.fields.all():
            field_name = f'field_{rf.pk}'
            if field_name not in form.cleaned_data:
                continue
            value = form.cleaned_data[field_name]
            answer = RegistrationAnswer(registration=registration, field=rf)
            if rf.field_type == 'file':
                file_obj = request.FILES.get(field_name)
                if file_obj:
                    answer.file = file_obj
            elif isinstance(value, bool):
                answer.value = 'Si' if value else 'No'
            else:
                answer.value = str(value) if value else ''
            answer.save()

        if event.is_paid:
            return redirect('event_payment', registration_id=registration.id)

        # Iscrizione gratuita: manda subito la conferma
        _send_confirmation_email(registration)
        return redirect('event_registration_confirm', registration_id=registration.id)

    return render(request, 'events/detail.html', {
        'event': event,
        'reg_form': form,
        'paypal_client_id': getattr(settings, 'PAYPAL_CLIENT_ID', ''),
        'form_error': True,
    })


def event_payment(request, registration_id):
    registration = get_object_or_404(Registration, id=registration_id)
    return render(request, 'events/payment.html', {
        'registration': registration,
        'paypal_client_id': getattr(settings, 'PAYPAL_CLIENT_ID', ''),
        'cancelled': request.GET.get('annullato') == '1',
    })


def event_registration_confirm(request, registration_id):
    registration = get_object_or_404(Registration, id=registration_id)
    return render(request, 'events/registration_confirm.html', {
        'registration': registration,
    })


def _get_paypal_token():
    if not settings.PAYPAL_CLIENT_ID or not settings.PAYPAL_CLIENT_SECRET:
        raise RuntimeError('Credenziali PayPal non configurate')

    mode = getattr(settings, 'PAYPAL_MODE', 'sandbox')
    base = 'https://api-m.sandbox.paypal.com' if mode == 'sandbox' else 'https://api-m.paypal.com'
    resp = requests.post(
        f'{base}/v1/oauth2/token',
        auth=(settings.PAYPAL_CLIENT_ID, settings.PAYPAL_CLIENT_SECRET),
        data={'grant_type': 'client_credentials'},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()['access_token'], base


def _payment_error_page(request, registration, message):
    return render(request, 'events/payment.html', {
        'registration': registration,
        'paypal_client_id': getattr(settings, 'PAYPAL_CLIENT_ID', ''),
        'payment_error': message,
    })


@require_POST
def paypal_start(request, registration_id):
    """Crea l'ordine PayPal e reindirizza l'utente alla pagina di pagamento di
    PayPal (flusso a redirect: nessun popup, nessun JS SDK)."""
    registration = get_object_or_404(Registration, id=registration_id, payment_status='pending')
    try:
        token, base = _get_paypal_token()
        amount_value = f'{registration.amount_paid:.2f}'
        description = f'Iscrizione: {registration.event.title}'[:127]
        return_url = request.build_absolute_uri(
            reverse('paypal_return', args=[registration.id])
        )
        cancel_url = request.build_absolute_uri(
            reverse('event_payment', args=[registration.id]) + '?annullato=1'
        )
        resp = requests.post(
            f'{base}/v2/checkout/orders',
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json',
                'PayPal-Request-Id': str(uuid.uuid4()),
            },
            json={
                'intent': 'CAPTURE',
                'purchase_units': [{
                    'amount': {'currency_code': 'EUR', 'value': amount_value},
                    'description': description,
                    'custom_id': str(registration.id),
                }],
                'application_context': {
                    'brand_name': 'Polisportiva Sanmarinese',
                    'shipping_preference': 'NO_SHIPPING',
                    'user_action': 'PAY_NOW',
                    'return_url': return_url,
                    'cancel_url': cancel_url,
                },
            },
            timeout=10,
        )
        if not resp.ok:
            payload = _paypal_error_payload(resp)
            logger.error('PayPal create order error %s: %s', resp.status_code, payload)
            return _payment_error_page(request, registration, payload['error'])

        data = resp.json()
        approve_url = next(
            (link['href'] for link in data.get('links', [])
             if link.get('rel') in ('approve', 'payer-action')),
            None,
        )
        if not approve_url:
            logger.error('PayPal: link di approvazione mancante nella risposta: %s', data)
            return _payment_error_page(
                request, registration,
                'Impossibile avviare il pagamento PayPal. Riprova o contattaci.',
            )

        registration.paypal_order_id = data.get('id', '')
        registration.save()
        return redirect(approve_url)
    except Exception as e:
        logger.error('PayPal start error: %s', e)
        return _payment_error_page(request, registration, str(e))


def paypal_return(request, registration_id):
    """PayPal reindirizza qui dopo l'approvazione: catturiamo il pagamento e
    portiamo l'utente alla pagina di conferma."""
    registration = get_object_or_404(Registration, id=registration_id)

    # Già elaborata (es. refresh del ritorno): non ricatturare, vai alla conferma.
    if registration.payment_status != 'pending':
        return redirect('event_registration_confirm', registration_id=registration.id)

    order_id = request.GET.get('token')
    if not order_id:
        # Ritorno senza token = pagamento non avviato/annullato.
        return redirect(reverse('event_payment', args=[registration.id]) + '?annullato=1')

    try:
        token, base = _get_paypal_token()
        resp = requests.post(
            f'{base}/v2/checkout/orders/{order_id}/capture',
            headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
            timeout=10,
        )
        if not resp.ok:
            payload = _paypal_error_payload(resp)
            logger.error('PayPal capture error %s: %s', resp.status_code, payload)
            return _payment_error_page(request, registration, payload['error'])

        result = resp.json()

        # Sicurezza: l'ordine catturato deve appartenere a questa iscrizione.
        custom_id = _extract_custom_id(result)
        if custom_id and custom_id != str(registration.id):
            logger.error(
                'PayPal: custom_id %s non corrisponde all\'iscrizione %s',
                custom_id, registration.id,
            )
            return _payment_error_page(
                request, registration, 'Pagamento non valido per questa iscrizione.'
            )

        capture_status = _extract_capture_status(result)

        if capture_status == 'COMPLETED':
            registration.payment_status = 'completed'
        elif capture_status == 'PENDING':
            # Accettato ma in revisione di sicurezza da PayPal: teniamo il posto
            # e avvisiamo l'utente in attesa che la verifica si chiuda.
            registration.payment_status = 'review'
        else:
            logger.warning(
                'PayPal capture non riuscita per iscrizione %s: stato cattura=%s',
                registration.id, capture_status,
            )
            registration.payment_status = 'failed'
            registration.save()
            return _payment_error_page(
                request, registration,
                'Il pagamento non è andato a buon fine. Riprova o contattaci.',
            )

        registration.paypal_order_id = order_id
        registration.save()
        _send_confirmation_email(registration)
        return redirect('event_registration_confirm', registration_id=registration.id)
    except Exception as e:
        logger.error('PayPal return/capture error: %s', e)
        return _payment_error_page(request, registration, str(e))
