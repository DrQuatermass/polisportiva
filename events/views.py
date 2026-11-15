import json
import logging
import os
import uuid

import requests
from django.conf import settings
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.views.generic import DetailView, ListView

from config.social_images import social_image_response

from .emails import (
    send_admin_receipt_alert, send_confirmation_email as _send_confirmation_email,
    send_transfer_instructions,
)
from .forms import build_registration_form
from .models import BankTransferSettings, Event, Registration, RegistrationAnswer

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
        selected_options = list(form.cleaned_data.get('reg_options') or [])
        if selected_options:
            amount = event.compute_total(selected_options)
        else:
            amount = event.registration_price
        status = 'pending' if amount > 0 else 'free'
        registration = Registration.objects.create(
            event=event,
            email=email,
            payment_status=status,
            amount_paid=amount,
        )
        if selected_options:
            registration.options.set(selected_options)
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

        if status == 'pending':
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


RECEIPT_MAX_SIZE = 5 * 1024 * 1024
# Estensione → firme iniziali ammesse (controllo minimo sul contenuto reale).
RECEIPT_SIGNATURES = {
    '.pdf': (b'%PDF',),
    '.jpg': (b'\xff\xd8\xff',),
    '.jpeg': (b'\xff\xd8\xff',),
    '.png': (b'\x89PNG',),
}


def _payment_context(request, registration, **extra):
    context = {
        'registration': registration,
        'paypal_client_id': getattr(settings, 'PAYPAL_CLIENT_ID', ''),
        'cancelled': request.GET.get('annullato') == '1',
        'receipt_uploaded': request.GET.get('distinta') == '1',
        'transfer_allowed': (
            registration.payment_status == 'pending' and registration.bank_transfer_allowed()
        ),
    }
    if registration.is_bank_transfer or context['transfer_allowed']:
        context['bank'] = BankTransferSettings.load()
    context.update(extra)
    return context


# Stato che cambia (bonifico scelto, distinta caricata...): mai dalla cache per-site.
@never_cache
def event_payment(request, registration_id):
    registration = get_object_or_404(Registration, id=registration_id)
    return render(request, 'events/payment.html', _payment_context(request, registration))


def _unavailable_options(registration):
    return [o.title for o in registration.options.all() if not o.is_available]


@require_POST
def choose_bank_transfer(request, registration_id):
    """L'iscritto sceglie il bonifico: il posto resta riservato per alcuni
    giorni e riceve via email IBAN, importo e causale."""
    registration = get_object_or_404(Registration, id=registration_id, payment_status='pending')
    if not registration.bank_transfer_allowed():
        return _payment_error_page(
            request, registration, 'Il pagamento con bonifico non è disponibile per questa iscrizione.'
        )
    unavailable = _unavailable_options(registration)
    if unavailable:
        return _payment_error_page(
            request, registration,
            'Nel frattempo queste lezioni non sono più disponibili: '
            f'{", ".join(unavailable)}. Torna alla pagina dell\'evento e ripeti l\'iscrizione.',
        )
    registration.choose_bank_transfer()
    send_transfer_instructions(registration)
    return redirect('event_payment', registration_id=registration.id)


@require_POST
def upload_transfer_receipt(request, registration_id):
    """Caricamento (o ricaricamento) della distinta del bonifico."""
    registration = get_object_or_404(
        Registration, id=registration_id, payment_status__in=['transfer', 'transfer_review'],
    )
    upload = request.FILES.get('distinta')
    error = None
    if not upload:
        error = 'Seleziona il file della distinta.'
    else:
        ext = os.path.splitext(upload.name)[1].lower()
        head = upload.read(8)
        upload.seek(0)
        if ext not in RECEIPT_SIGNATURES or not head.startswith(RECEIPT_SIGNATURES[ext]):
            error = 'Formato non valido: carica un PDF, JPG o PNG.'
        elif upload.size > RECEIPT_MAX_SIZE:
            error = 'Il file è troppo grande (massimo 5 MB).'
    if error:
        return render(request, 'events/payment.html',
                      _payment_context(request, registration, upload_error=error))

    if registration.transfer_receipt:
        registration.transfer_receipt.delete(save=False)
    registration.transfer_receipt = upload
    registration.receipt_uploaded_at = timezone.now()
    registration.payment_status = 'transfer_review'
    registration.transfer_note = ''
    registration.save()
    send_admin_receipt_alert(registration)
    return redirect(reverse('event_payment', args=[registration.id]) + '?distinta=1')


@never_cache
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
    return render(request, 'events/payment.html',
                  _payment_context(request, registration, payment_error=message))


@require_POST
def paypal_start(request, registration_id):
    """Crea l'ordine PayPal e reindirizza l'utente alla pagina di pagamento di
    PayPal (flusso a redirect: nessun popup, nessun JS SDK)."""
    registration = get_object_or_404(Registration, id=registration_id, payment_status='pending')

    # Tra iscrizione e pagamento una lezione può essersi riempita o chiusa.
    unavailable = _unavailable_options(registration)
    if unavailable:
        return _payment_error_page(
            request, registration,
            'Nel frattempo queste lezioni non sono più disponibili: '
            f'{", ".join(unavailable)}. Torna alla pagina dell\'evento e ripeti l\'iscrizione.',
        )

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


# Eventi PayPal → nuovo stato dell'iscrizione.
_WEBHOOK_STATUS_MAP = {
    'PAYMENT.CAPTURE.COMPLETED': 'completed',
    'PAYMENT.CAPTURE.DENIED':    'failed',
    'PAYMENT.CAPTURE.REVERSED':  'cancelled',
    'PAYMENT.CAPTURE.REFUNDED':  'cancelled',
}


def _paypal_webhook_verified(request, event):
    """Verifica la firma della notifica con PayPal, per scartare eventi
    contraffatti."""
    webhook_id = getattr(settings, 'PAYPAL_WEBHOOK_ID', '')
    if not webhook_id:
        logger.error('PayPal webhook ricevuto ma PAYPAL_WEBHOOK_ID non è configurato')
        return False
    try:
        token, base = _get_paypal_token()
        resp = requests.post(
            f'{base}/v1/notifications/verify-webhook-signature',
            headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
            json={
                'auth_algo': request.headers.get('Paypal-Auth-Algo'),
                'cert_url': request.headers.get('Paypal-Cert-Url'),
                'transmission_id': request.headers.get('Paypal-Transmission-Id'),
                'transmission_sig': request.headers.get('Paypal-Transmission-Sig'),
                'transmission_time': request.headers.get('Paypal-Transmission-Time'),
                'webhook_id': webhook_id,
                'webhook_event': event,
            },
            timeout=10,
        )
        return resp.ok and resp.json().get('verification_status') == 'SUCCESS'
    except Exception as e:
        logger.error('PayPal webhook: verifica firma fallita: %s', e)
        return False


@csrf_exempt
@require_POST
def paypal_webhook(request):
    """Riceve le notifiche PayPal e aggiorna lo stato dell'iscrizione quando
    PayPal chiude la revisione (es. 'review' → 'completed'/'failed')."""
    try:
        event = json.loads(request.body)
    except ValueError:
        logger.error('PayPal webhook: body non JSON')
        return HttpResponse(status=400)

    if not _paypal_webhook_verified(request, event):
        logger.warning('PayPal webhook: firma non valida, evento ignorato')
        return HttpResponse(status=400)

    event_type = event.get('event_type', '')
    resource = event.get('resource') or {}
    custom_id = resource.get('custom_id')

    new_status = _WEBHOOK_STATUS_MAP.get(event_type)
    if not new_status or not custom_id:
        # Evento non pertinente o senza riferimento all'iscrizione: ignora.
        return HttpResponse(status=200)

    try:
        registration = Registration.objects.get(id=custom_id)
    except (Registration.DoesNotExist, ValidationError, ValueError):
        logger.warning('PayPal webhook: iscrizione %s non trovata', custom_id)
        return HttpResponse(status=200)

    if registration.payment_status != new_status:
        old_status = registration.payment_status
        registration.payment_status = new_status
        registration.save(update_fields=['payment_status'])
        logger.info(
            'PayPal webhook: iscrizione %s %s → %s (%s)',
            registration.id, old_status, new_status, event_type,
        )
        # Verifica chiusa positivamente: conferma l'iscritto via email.
        if new_status == 'completed':
            _send_confirmation_email(registration)

    return HttpResponse(status=200)
