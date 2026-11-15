import re
import uuid
from decimal import Decimal
from html import unescape

from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.html import strip_tags

from config.image_utils import optimize_image_field

# Stati che occupano un posto (gratuito, pagato, o pagato ma in verifica PayPal).
CONFIRMED_STATUSES = ['free', 'completed', 'review']


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
        if self.has_options and not any(o.is_available for o in self.options.all()):
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
    def options_total_price(self):
        return sum((o.price for o in self.options.all()), Decimal('0'))

    @property
    def bundle_available(self):
        """Il pacchetto completo è acquistabile solo se tutte le opzioni lo sono."""
        options = list(self.options.all())
        return bool(options) and self.bundle_price is not None and all(o.is_available for o in options)

    @property
    def min_price(self):
        if self.has_options:
            return min(o.price for o in self.options.all())
        return self.registration_price

    def compute_total(self, selected_options):
        """Totale da pagare per le opzioni scelte (calcolato sempre lato server).
        Se sono scelte tutte le opzioni e c'è un prezzo pacchetto, si applica
        quello (mai più della somma delle singole)."""
        selected = list(selected_options)
        total = sum((o.price for o in selected), Decimal('0'))
        all_ids = set(self.options.values_list('pk', flat=True))
        if self.bundle_price is not None and all_ids and {o.pk for o in selected} == all_ids:
            total = min(total, self.bundle_price)
        return total


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
    date = models.DateTimeField(verbose_name='Data e ora')
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
        return f'{self.event} – {self.date:%d/%m} {self.title}'

    @property
    def participants_count(self):
        return self.registrations.filter(payment_status__in=CONFIRMED_STATUSES).count()

    @property
    def is_full(self):
        return self.max_participants is not None and self.participants_count >= self.max_participants

    @property
    def is_closed(self):
        return timezone.now() >= (self.registration_deadline or self.date)

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


class RegistrationAnswer(models.Model):
    registration = models.ForeignKey(Registration, on_delete=models.CASCADE, related_name='answers')
    field = models.ForeignKey(RegistrationField, on_delete=models.SET_NULL, null=True)
    value = models.TextField(blank=True, verbose_name='Valore')
    file = models.FileField(upload_to='registrations/', blank=True, null=True, verbose_name='File allegato')

    def __str__(self):
        label = self.field.label if self.field else '?'
        return f'{label}: {self.value or "(file)"}'
