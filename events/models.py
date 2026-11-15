import os
import re
import secrets
import uuid
from datetime import timedelta
from decimal import Decimal
from html import unescape

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.html import strip_tags

from config.image_utils import optimize_image_field

# Stati che occupano un posto: gratuito, pagato, pagato ma in verifica PayPal,
# o bonifico annunciato (in attesa o con distinta da verificare).
CONFIRMED_STATUSES = ['free', 'completed', 'review', 'transfer', 'transfer_review']


class PrivateStorage(FileSystemStorage):
    """Storage fuori da MEDIA_ROOT: i file non hanno un URL pubblico.
    La cartella è letta da settings a ogni accesso (utile anche nei test)."""

    @property
    def base_location(self):
        return str(settings.PRIVATE_MEDIA_ROOT)

    @property
    def location(self):
        return os.path.abspath(self.base_location)

    def url(self, name):
        raise ValueError('I file privati non hanno un URL pubblico.')


def private_storage():
    return PrivateStorage()


def attachment_upload_to(instance, filename):
    ext = os.path.splitext(filename)[1].lower()
    return f'allegati/{timezone.now():%Y/%m}/{uuid.uuid4().hex}{ext}'


def receipt_upload_to(instance, filename):
    ext = os.path.splitext(filename)[1].lower()
    return f'distinte/{timezone.now():%Y/%m}/{uuid.uuid4().hex}{ext}'


class Event(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    date = models.DateTimeField()
    location = models.CharField(max_length=200)
    image = models.ImageField(upload_to='events/', blank=True, null=True)
    published = models.BooleanField(default=True, verbose_name='Pubblicato')

    # --- SEO ---
    meta_description = models.CharField(
        max_length=160,
        blank=True,
        verbose_name='Meta description',
        help_text='Testo mostrato da Google e social (max 160 caratteri). '
                  'Se vuoto viene generato dalla descrizione.',
    )
    og_image = models.ImageField(
        upload_to='events/og/',
        blank=True,
        null=True,
        verbose_name='Immagine social (opzionale)',
        help_text='1200x630 consigliato. Se vuoto usa l\'immagine principale.',
    )

    registration_enabled = models.BooleanField(default=False, verbose_name='Abilita iscrizioni')
    registration_deadline = models.DateTimeField(blank=True, null=True, verbose_name='Scadenza iscrizioni', help_text='Lascia vuoto per nessuna scadenza')
    max_registrations = models.PositiveIntegerField(blank=True, null=True, verbose_name='Posti massimi', help_text='Lascia vuoto per illimitato')
    registration_price = models.DecimalField(max_digits=8, decimal_places=2, default=0, verbose_name='Quota iscrizione (EUR)', help_text='0 = gratuito')
    registration_notes = models.TextField(blank=True, verbose_name='Note per gli iscritti', help_text='Testo mostrato sopra il form')
    accept_bank_transfer = models.BooleanField(
        default=False, verbose_name='Accetta bonifico',
        help_text='Oltre a PayPal, permette di pagare con bonifico bancario '
                  '(IBAN e regole in "Dati per il bonifico").',
    )
    bundle_price = models.DecimalField(
        max_digits=8, decimal_places=2, blank=True, null=True,
        verbose_name='Prezzo pacchetto completo (EUR)',
        help_text='Solo per eventi con lezioni/opzioni: prezzo se si scelgono tutte. '
                  'Lascia vuoto per nessuno sconto.',
    )

    class Meta:
        ordering = ['date']
        verbose_name = 'Evento'
        verbose_name_plural = 'Eventi'

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('event_detail', kwargs={'slug': self.slug})

    def save(self, *args, **kwargs):
        optimize_image_field(self, 'image')
        optimize_image_field(self, 'og_image', max_size=(1200, 630))
        super().save(*args, **kwargs)

    def get_meta_description(self):
        text = unescape(self.meta_description or strip_tags(self.description or ''))
        text = re.sub(r'https?://\S+', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        if not text and self.meta_description:
            text = unescape(strip_tags(self.description or ''))
            text = re.sub(r'https?://\S+', '', text)
            text = re.sub(r'\s+', ' ', text).strip()
        return text[:157] + '…' if len(text) > 160 else text

    def get_og_image_url(self):
        if self.og_image:
            return self.og_image.url
        if self.image:
            return self.image.url
        return ''

    @property
    def registrations_open(self):
        if not self.registration_enabled:
            return False
        if self.registration_deadline and timezone.now() > self.registration_deadline:
            return False
        if self.max_registrations is not None:
            confirmed = self.registrations.filter(payment_status__in=CONFIRMED_STATUSES).count()
            if confirmed >= self.max_registrations:
                return False
        if self.has_options and not any(o.is_available for o in self.lessons):
            return False
        return True

    @property
    def registrations_count(self):
        return self.registrations.filter(payment_status__in=CONFIRMED_STATUSES).count()

    @property
    def has_options(self):
        return self.options.exists()

    @property
    def is_paid(self):
        if self.has_options:
            return any(o.price > 0 for o in self.options.all())
        return self.registration_price > 0

    @property
    def lessons(self):
        """Opzioni che sono lezioni (escluse le voci extra come la tessera)."""
        return [o for o in self.options.all() if not o.is_extra]

    @property
    def extras(self):
        return [o for o in self.options.all() if o.is_extra]

    @property
    def options_total_price(self):
        """Somma delle sole lezioni (base del confronto col prezzo pacchetto)."""
        return sum((o.price for o in self.lessons), Decimal('0'))

    @property
    def bundle_available(self):
        """Il pacchetto completo è acquistabile solo se tutte le lezioni lo sono."""
        lessons = self.lessons
        return bool(lessons) and self.bundle_price is not None and all(o.is_available for o in lessons)

    @property
    def min_price(self):
        prices = [o.price for o in (self.lessons or self.options.all())]
        return min(prices) if prices else self.registration_price

    def compute_total(self, selected_options):
        """Totale da pagare per le opzioni scelte (calcolato sempre lato server).
        Se sono scelte tutte le lezioni e c'è un prezzo pacchetto, si applica
        quello (mai più della somma delle singole); le voci extra si sommano."""
        selected = list(selected_options)
        lessons = [o for o in selected if not o.is_extra]
        extras = [o for o in selected if o.is_extra]
        total = sum((o.price for o in lessons), Decimal('0'))
        all_ids = {o.pk for o in self.lessons}
        if self.bundle_price is not None and all_ids and {o.pk for o in lessons} == all_ids:
            total = min(total, self.bundle_price)
        return total + sum((o.price for o in extras), Decimal('0'))


class EventImage(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='gallery_images')
    image = models.ImageField(upload_to='events/gallery/', verbose_name='Foto')
    caption = models.CharField(max_length=200, blank=True, verbose_name='Didascalia')
    order = models.PositiveIntegerField(default=0, verbose_name='Ordine')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Data caricamento')

    class Meta:
        ordering = ['order', 'id']
        verbose_name = 'Foto evento'
        verbose_name_plural = 'Foto evento'

    def __str__(self):
        return self.caption or f'Foto: {self.event}'

    def save(self, *args, **kwargs):
        optimize_image_field(self, 'image')
        super().save(*args, **kwargs)


class EventOption(models.Model):
    """Lezione/giornata/modulo di un evento, selezionabile singolarmente
    nel form di iscrizione, con prezzo e posti propri."""
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='options')
    title = models.CharField(max_length=200, verbose_name='Titolo')
    is_extra = models.BooleanField(
        default=False, verbose_name='Extra',
        help_text='Non è una lezione (es. tessera, maglietta): si aggiunge al totale, '
                  'non conta per il prezzo pacchetto e non si può scegliere da sola.',
    )
    date = models.DateTimeField(
        blank=True, null=True, verbose_name='Data e ora',
        help_text='Obbligatoria per le lezioni; facoltativa per gli extra.',
    )
    price = models.DecimalField(max_digits=8, decimal_places=2, default=0, verbose_name='Prezzo (EUR)')
    max_participants = models.PositiveIntegerField(
        blank=True, null=True, verbose_name='Posti max',
        help_text='Vuoto = illimitati',
    )
    registration_deadline = models.DateTimeField(
        blank=True, null=True, verbose_name='Chiusura iscrizioni',
        help_text='Vuoto = si chiude all\'inizio della lezione',
    )
    order = models.PositiveIntegerField(default=0, verbose_name='Ordine')

    class Meta:
        ordering = ['order', 'date', 'id']
        verbose_name = 'Lezione / opzione'
        verbose_name_plural = 'Lezioni / opzioni'

    def __str__(self):
        if self.date:
            return f'{self.event} – {timezone.localtime(self.date):%d/%m} {self.title}'
        return f'{self.event} – {self.title}'

    def clean(self):
        from django.core.exceptions import ValidationError
        if not self.is_extra and not self.date:
            raise ValidationError({'date': 'Indica data e ora della lezione.'})

    @property
    def participants_count(self):
        return self.registrations.filter(payment_status__in=CONFIRMED_STATUSES).count()

    @property
    def is_full(self):
        return self.max_participants is not None and self.participants_count >= self.max_participants

    @property
    def is_closed(self):
        closes_at = self.registration_deadline or self.date
        return closes_at is not None and timezone.now() >= closes_at

    @property
    def is_available(self):
        return not self.is_closed and not self.is_full

    @property
    def places_left(self):
        if self.max_participants is None:
            return None
        return max(self.max_participants - self.participants_count, 0)


class RegistrationField(models.Model):
    FIELD_TYPES = [
        ('text',     'Testo breve'),
        ('email',    'Email'),
        ('phone',    'Telefono'),
        ('textarea', 'Testo lungo'),
        ('select',   'Scelta singola (dropdown)'),
        ('radio',    'Scelta singola (radio button)'),
        ('checkbox', 'Casella di spunta'),
        ('file',     'Allegato (PDF / immagine)'),
        ('date',     'Data'),
        ('number',   'Numero'),
    ]

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='fields')
    field_type = models.CharField(max_length=20, choices=FIELD_TYPES, verbose_name='Tipo campo')
    label = models.CharField(max_length=200, verbose_name='Etichetta')
    help_text = models.CharField(max_length=500, blank=True, verbose_name='Testo di aiuto')
    required = models.BooleanField(default=True, verbose_name='Obbligatorio')
    order = models.PositiveIntegerField(default=0, verbose_name='Ordine')
    options = models.TextField(blank=True, verbose_name='Opzioni', help_text='Solo per select/radio: una voce per riga')

    class Meta:
        ordering = ['order', 'id']
        verbose_name = 'Campo iscrizione'
        verbose_name_plural = 'Campi iscrizione'

    def __str__(self):
        return f'{self.event} - {self.label}'

    def get_options_list(self):
        return [o.strip() for o in self.options.splitlines() if o.strip()]


class Registration(models.Model):
    PAYMENT_STATUS = [
        ('free',      'Gratuito'),
        ('pending',   'In attesa di pagamento'),
        ('review',    'In verifica PayPal'),
        ('transfer',  'In attesa di bonifico'),
        ('transfer_review', 'Distinta da verificare'),
        ('completed', 'Pagamento completato'),
        ('failed',    'Pagamento fallito'),
        ('cancelled', 'Annullato'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='registrations')
    email = models.EmailField(verbose_name='Email')
    submitted_at = models.DateTimeField(auto_now_add=True, verbose_name='Data iscrizione')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='free', verbose_name='Stato pagamento')
    paypal_order_id = models.CharField(max_length=200, blank=True)
    amount_paid = models.DecimalField(max_digits=8, decimal_places=2, default=0, verbose_name='Importo pagato (EUR)')
    options = models.ManyToManyField(
        EventOption, blank=True, related_name='registrations', verbose_name='Lezioni scelte',
    )

    # --- Bonifico ---
    transfer_code = models.CharField(
        max_length=12, blank=True, db_index=True, verbose_name='Codice bonifico',
        help_text='Da cercare nella causale del bonifico',
    )
    transfer_chosen_at = models.DateTimeField(blank=True, null=True, verbose_name='Bonifico scelto il')
    transfer_receipt = models.FileField(
        upload_to=receipt_upload_to, storage=private_storage, blank=True,
        verbose_name='Distinta bonifico',
    )
    receipt_uploaded_at = models.DateTimeField(blank=True, null=True, verbose_name='Distinta caricata il')
    transfer_note = models.TextField(
        blank=True, verbose_name="Nota per l'iscritto",
        help_text="Motivo del rifiuto della distinta: viene inviato all'iscritto via email.",
    )

    class Meta:
        ordering = ['-submitted_at']
        verbose_name = 'Iscrizione'
        verbose_name_plural = 'Iscrizioni'

    def __str__(self):
        return f'{self.event} - {self.email} [{self.get_payment_status_display()}]'

    @property
    def is_confirmed(self):
        return self.payment_status in ('free', 'completed')

    @property
    def is_under_review(self):
        return self.payment_status == 'review'

    @property
    def bundle_applied(self):
        """True se sono state scelte tutte le lezioni con lo sconto pacchetto."""
        event = self.event
        lessons = {o.pk for o in event.lessons}
        chosen = {o.pk for o in self.options.all() if not o.is_extra}
        return (event.bundle_price is not None and bool(lessons) and chosen == lessons
                and event.bundle_price < event.options_total_price)

    @property
    def is_bank_transfer(self):
        return self.payment_status in ('transfer', 'transfer_review')

    @property
    def transfer_reference(self):
        """Causale da indicare nel bonifico."""
        return f'ISCR {self.transfer_code} {self.event.title}'[:140]

    @property
    def transfer_deadline(self):
        if not self.transfer_chosen_at:
            return None
        return self.transfer_chosen_at + timedelta(days=BankTransferSettings.load().hold_days)

    @property
    def transfer_overdue(self):
        deadline = self.transfer_deadline
        return self.payment_status == 'transfer' and deadline is not None and timezone.now() > deadline

    @property
    def first_activity_date(self):
        """Data della prima lezione scelta (o dell'evento)."""
        dates = [o.date for o in self.options.all() if o.date and not o.is_extra]
        return min(dates) if dates else self.event.date

    def bank_transfer_allowed(self):
        """Il bonifico si può scegliere solo se l'evento lo accetta, i dati
        bancari sono configurati e c'è abbastanza tempo prima dell'inizio."""
        if not self.event.accept_bank_transfer:
            return False
        bank = BankTransferSettings.load()
        if not bank.is_configured:
            return False
        return timezone.now() + timedelta(days=bank.min_days_before) <= self.first_activity_date

    def choose_bank_transfer(self):
        if not self.transfer_code:
            self.transfer_code = secrets.token_hex(3).upper()
        self.payment_status = 'transfer'
        self.transfer_chosen_at = timezone.now()
        self.save(update_fields=['transfer_code', 'payment_status', 'transfer_chosen_at'])


class RegistrationAnswer(models.Model):
    registration = models.ForeignKey(Registration, on_delete=models.CASCADE, related_name='answers')
    field = models.ForeignKey(RegistrationField, on_delete=models.SET_NULL, null=True)
    value = models.TextField(blank=True, verbose_name='Valore')
    # Privato come le distinte: certificati e documenti degli iscritti non
    # devono essere raggiungibili da un URL pubblico.
    file = models.FileField(
        upload_to=attachment_upload_to, storage=private_storage,
        blank=True, null=True, verbose_name='File allegato',
    )

    def __str__(self):
        label = self.field.label if self.field else '?'
        return f'{label}: {self.value or "(file)"}'


class BankTransferSettings(models.Model):
    """Dati per il bonifico, unici per tutto il sito (modificabili dall'admin)."""
    beneficiary = models.CharField(max_length=200, blank=True, verbose_name='Intestatario')
    iban = models.CharField(max_length=40, blank=True, verbose_name='IBAN')
    bank_name = models.CharField(max_length=200, blank=True, verbose_name='Banca')
    hold_days = models.PositiveIntegerField(
        default=5, verbose_name='Giorni per pagare',
        help_text='Per quanti giorni il posto resta riservato a chi sceglie il bonifico.',
    )
    min_days_before = models.PositiveIntegerField(
        default=3, verbose_name="Giorni minimi prima dell'inizio",
        help_text='Se la prima lezione/evento è più vicina di così, il bonifico non viene proposto.',
    )
    notify_email = models.EmailField(
        blank=True, verbose_name='Email per gli avvisi',
        help_text='Riceve un avviso quando un iscritto carica la distinta. '
                  'Vuoto = indirizzo contatti del sito.',
    )
    instructions = models.TextField(
        blank=True, verbose_name='Istruzioni aggiuntive',
        help_text='Testo facoltativo mostrato sotto i dati del bonifico.',
    )

    class Meta:
        verbose_name = 'Dati per il bonifico'
        verbose_name_plural = 'Dati per il bonifico'

    def __str__(self):
        return 'Dati per il bonifico'

    def save(self, *args, **kwargs):
        self.pk = 1
        self.iban = self.iban.replace(' ', '').upper()
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    @property
    def is_configured(self):
        return bool(self.iban and self.beneficiary)

    @property
    def iban_display(self):
        return ' '.join(self.iban[i:i + 4] for i in range(0, len(self.iban), 4))

    @property
    def alert_email(self):
        return self.notify_email or settings.CONTACT_EMAIL
