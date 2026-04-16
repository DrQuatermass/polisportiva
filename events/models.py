import uuid
from django.db import models
from django.utils import timezone


class Event(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    date = models.DateTimeField()
    location = models.CharField(max_length=200)
    image = models.ImageField(upload_to='events/', blank=True, null=True)
    published = models.BooleanField(default=True, verbose_name='Pubblicato')

    registration_enabled = models.BooleanField(default=False, verbose_name='Abilita iscrizioni')
    registration_deadline = models.DateTimeField(blank=True, null=True, verbose_name='Scadenza iscrizioni', help_text='Lascia vuoto per nessuna scadenza')
    max_registrations = models.PositiveIntegerField(blank=True, null=True, verbose_name='Posti massimi', help_text='Lascia vuoto per illimitato')
    registration_price = models.DecimalField(max_digits=8, decimal_places=2, default=0, verbose_name='Quota iscrizione (EUR)', help_text='0 = gratuito')
    registration_notes = models.TextField(blank=True, verbose_name='Note per gli iscritti', help_text='Testo mostrato sopra il form')

    class Meta:
        ordering = ['date']
        verbose_name = 'Evento'
        verbose_name_plural = 'Eventi'

    def __str__(self):
        return self.title

    @property
    def registrations_open(self):
        if not self.registration_enabled:
            return False
        if self.registration_deadline and timezone.now() > self.registration_deadline:
            return False
        if self.max_registrations is not None:
            confirmed = self.registrations.filter(payment_status__in=['free', 'completed']).count()
            if confirmed >= self.max_registrations:
                return False
        return True

    @property
    def registrations_count(self):
        return self.registrations.filter(payment_status__in=['free', 'completed']).count()

    @property
    def is_paid(self):
        return self.registration_price > 0


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

    class Meta:
        ordering = ['-submitted_at']
        verbose_name = 'Iscrizione'
        verbose_name_plural = 'Iscrizioni'

    def __str__(self):
        return f'{self.event} - {self.email} [{self.get_payment_status_display()}]'

    @property
    def is_confirmed(self):
        return self.payment_status in ('free', 'completed')


class RegistrationAnswer(models.Model):
    registration = models.ForeignKey(Registration, on_delete=models.CASCADE, related_name='answers')
    field = models.ForeignKey(RegistrationField, on_delete=models.SET_NULL, null=True)
    value = models.TextField(blank=True, verbose_name='Valore')
    file = models.FileField(upload_to='registrations/', blank=True, null=True, verbose_name='File allegato')

    def __str__(self):
        label = self.field.label if self.field else '?'
        return f'{label}: {self.value or "(file)"}'
