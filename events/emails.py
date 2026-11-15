"""Email inviate dal flusso di iscrizione (conferme, bonifico, distinte)."""
import logging

from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse
from django.utils import timezone

from .models import BankTransferSettings

logger = logging.getLogger(__name__)

SIGNATURE = 'Polisportiva Sanmarinese di Carpi'


def _site_url(path):
    return settings.SITE_URL.rstrip('/' + chr(92)) + path


def _send(registration, subject, body, recipient=None):
    try:
        send_mail(
            subject=subject,
            message=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient or registration.email],
            fail_silently=False,
        )
    except Exception as e:
        logger.error('Errore invio email "%s" (iscrizione %s): %s', subject, registration.id, e)


def _summary(registration, with_amount=True):
    """Lezioni scelte (o data evento) e importo."""
    event = registration.event
    lines = ''
    options = list(registration.options.all())
    if options:
        lines += '\nLezioni scelte:\n'
        for option in options:
            if option.date and not option.is_extra:
                local_date = timezone.localtime(option.date)
                lines += f'  - {local_date.strftime("%d/%m/%Y %H:%M")} {option.title}\n'
            else:
                lines += f'  - {option.title}\n'
        lines += '\n'
    elif event.date:
        lines += f'Data evento: {timezone.localtime(event.date).strftime("%d/%m/%Y %H:%M")}\n'
    if with_amount and registration.amount_paid:
        lines += f'Importo: € {registration.amount_paid}\n'
    return lines


def send_confirmation_email(registration):
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

    body = (
        f'Ciao,\n\n'
        f'la tua iscrizione all\'evento "{event.title}" è stata ricevuta con successo.\n'
    )
    body += _summary(registration)
    if payment_note:
        body += f'{payment_note}\n'
    body += (
        f'\nNumero iscrizione: {registration.id}\n\n'
        f'Per qualsiasi informazione contattaci a {settings.CONTACT_EMAIL}.\n\n'
        f'{SIGNATURE}'
    )
    _send(registration, f'Conferma iscrizione: {event.title}', body)


def _bank_details(registration):
    bank = BankTransferSettings.load()
    text = (
        f'Intestatario: {bank.beneficiary}\n'
        f'IBAN: {bank.iban_display}\n'
    )
    if bank.bank_name:
        text += f'Banca: {bank.bank_name}\n'
    text += (
        f'Importo: € {registration.amount_paid}\n'
        f'Causale: {registration.transfer_reference}\n'
    )
    deadline = registration.transfer_deadline
    if deadline:
        text += f'Da effettuare entro: {timezone.localtime(deadline).strftime("%d/%m/%Y")}\n'
    if bank.instructions:
        text += f'\n{bank.instructions}\n'
    return text


def send_transfer_instructions(registration):
    event = registration.event
    payment_url = _site_url(reverse('event_payment', args=[registration.id]))
    body = (
        f'Ciao,\n\n'
        f'abbiamo registrato la tua iscrizione a "{event.title}" con pagamento tramite bonifico.\n'
        f'{_summary(registration, with_amount=False)}\n'
        f'Dati per il bonifico:\n\n'
        f'{_bank_details(registration)}\n'
        f'Il posto resta riservato fino alla scadenza indicata. Dopo aver fatto il bonifico '
        f'puoi caricare la distinta da questa pagina (facoltativo, ma ci aiuta a confermarti prima):\n'
        f'{payment_url}\n\n'
        f'Riceverai la conferma definitiva appena verificato il pagamento.\n\n'
        f'Per qualsiasi informazione contattaci a {settings.CONTACT_EMAIL}.\n\n'
        f'{SIGNATURE}'
    )
    _send(registration, f'Iscrizione {event.title}: dati per il bonifico', body)


def send_admin_receipt_alert(registration):
    bank = BankTransferSettings.load()
    admin_url = _site_url(reverse('admin:events_registration_change', args=[registration.id]))
    body = (
        f'{registration.email} ha caricato la distinta del bonifico.\n\n'
        f'Evento: {registration.event.title}\n'
        f'{_summary(registration)}'
        f'Codice bonifico: {registration.transfer_code}\n\n'
        f'Verifica e conferma da qui:\n{admin_url}\n'
    )
    _send(
        registration,
        f'Distinta da verificare: {registration.event.title} ({registration.transfer_code})',
        body,
        recipient=bank.alert_email,
    )


def send_receipt_rejected(registration):
    event = registration.event
    payment_url = _site_url(reverse('event_payment', args=[registration.id]))
    body = (
        f'Ciao,\n\n'
        f'non siamo riusciti a verificare la distinta del bonifico per "{event.title}".\n'
    )
    if registration.transfer_note:
        body += f'\nMotivo: {registration.transfer_note}\n'
    body += (
        f'\nPuoi caricarne una nuova da qui:\n{payment_url}\n\n'
        f'Riepilogo dati per il bonifico:\n\n{_bank_details(registration)}\n'
        f'Per qualsiasi informazione contattaci a {settings.CONTACT_EMAIL}.\n\n'
        f'{SIGNATURE}'
    )
    _send(registration, f'Iscrizione {event.title}: distinta da ricaricare', body)
