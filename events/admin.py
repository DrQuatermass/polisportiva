import csv
from urllib.parse import urljoin

from django.conf import settings
from django import forms
from django.contrib import admin
from django.contrib import messages
from django.http import FileResponse, Http404, HttpResponse, HttpResponseRedirect
from django.urls import path, reverse
from django.utils import timezone
from django.utils.html import format_html
from ckeditor.widgets import CKEditorWidget

from .emails import send_confirmation_email, send_receipt_rejected
from .models import (
    BankTransferSettings, Event, EventImage, EventOption, Registration, RegistrationAnswer,
    RegistrationField,
)


class EventAdminForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = '__all__'
        widgets = {
            'description': CKEditorWidget(),
        }


class RegistrationFieldInline(admin.TabularInline):
    model = RegistrationField
    extra = 1
    fields = ['order', 'field_type', 'label', 'required', 'options', 'help_text']
    ordering = ['order']


class EventOptionInline(admin.TabularInline):
    model = EventOption
    extra = 0
    fields = ['order', 'date', 'title', 'price', 'max_participants', 'registration_deadline', 'iscritti']
    readonly_fields = ['iscritti']
    ordering = ['order', 'date']
    verbose_name_plural = (
        'Lezioni / opzioni selezionabili (lascia vuoto per un evento classico a prezzo unico)'
    )

    def iscritti(self, obj):
        if not obj.pk:
            return '-'
        n = obj.participants_count
        label = f'{n} / {obj.max_participants}' if obj.max_participants else str(n)
        url = reverse('admin:events_registration_changelist') + f'?options__id__exact={obj.pk}'
        return format_html('<a href="{}">{}</a>', url, label)
    iscritti.short_description = 'Iscritti'


class EventImageInline(admin.TabularInline):
    model = EventImage
    extra = 3
    fields = ['order', 'image', 'caption', 'preview']
    readonly_fields = ['preview']
    ordering = ['order', 'id']

    def preview(self, obj):
        if not obj.pk or not obj.image:
            return '-'
        return format_html(
            '<img src="{}" alt="" style="width:120px;height:68px;object-fit:cover;border-radius:4px;">',
            obj.image.url,
        )
    preview.short_description = 'Anteprima'


class RegistrationAnswerInline(admin.TabularInline):
    model = RegistrationAnswer
    extra = 0
    readonly_fields = ['field_label', 'value', 'file']
    fields = ['field_label', 'value', 'file']
    can_delete = False

    def field_label(self, obj):
        return obj.field.label if obj.field else '-'
    field_label.short_description = 'Campo'

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    form = EventAdminForm
    list_display = ['title', 'date', 'location', 'published', 'registration_enabled',
                    'registration_price', 'iscritti', 'facebook_share']
    list_filter = ['published', 'date', 'registration_enabled']
    search_fields = ['title', 'description', 'location']
    ordering = ['date']
    prepopulated_fields = {'slug': ('title',)}
    inlines = [EventOptionInline, EventImageInline, RegistrationFieldInline]

    fieldsets = [
        ('Evento', {
            'fields': ['title', 'slug', 'description', 'date', 'location', 'image', 'published'],
        }),
        ('SEO & Social', {
            'fields': ['meta_description', 'og_image'],
            'classes': ['collapse'],
            'description': 'Personalizza come appare l\'evento su Google, Facebook e WhatsApp.',
        }),
        ('Iscrizioni', {
            'fields': [
                'registration_enabled',
                'registration_deadline',
                'max_registrations',
                'registration_price',
                'bundle_price',
                'accept_bank_transfer',
                'registration_notes',
            ],
            'classes': ['collapse'],
            'description': 'Evento a prezzo unico: usa "Quota iscrizione". '
                           'Evento a lezioni (es. corso): aggiungi le lezioni nella tabella '
                           '"Lezioni / opzioni" più sotto; la quota unica viene ignorata e '
                           'puoi indicare un prezzo pacchetto per chi le sceglie tutte.',
        }),
    ]

    def iscritti(self, obj):
        n = obj.registrations_count
        if obj.max_registrations:
            return f'{n} / {obj.max_registrations}'
        return n
    iscritti.short_description = 'Iscritti'

    def facebook_share(self, obj):
        site = getattr(settings, 'SITE_URL', '').rstrip('/\\')
        page_url = getattr(settings, 'FACEBOOK_PAGE_URL', 'https://www.facebook.com/')
        url = urljoin(f'{site}/', obj.get_absolute_url().lstrip('/'))
        return format_html(
            '<div style="display:flex;gap:6px;align-items:center;white-space:nowrap;">'
            '<button type="button" data-url="{}" onclick="navigator.clipboard.writeText(this.dataset.url);this.textContent=\'Copiato\';" '
            'style="border:0;background:#198754;color:#fff;padding:4px 10px;border-radius:5px;font-size:0.82em;font-weight:600;cursor:pointer;">'
            'Copia link</button>'
            '<a href="{}" target="_blank" rel="noopener" '
            'style="display:inline-flex;align-items:center;background:#0d6efd;color:#fff;padding:4px 10px;border-radius:5px;'
            'text-decoration:none;font-size:0.82em;font-weight:600;">Pagina</a>'
            '</div>',
            url,
            page_url,
        )
    facebook_share.short_description = 'Facebook'
    facebook_share.allow_tags = True


class OptionFilter(admin.SimpleListFilter):
    """Filtro per lezione: mostra solo le lezioni dell'evento già filtrato
    (o tutte, se nessun evento è selezionato)."""
    title = 'lezione'
    parameter_name = 'options__id__exact'

    def lookups(self, request, model_admin):
        qs = EventOption.objects.select_related('event').order_by('event__date', 'order', 'date')
        event_id = request.GET.get('event__id__exact')
        if event_id:
            qs = qs.filter(event_id=event_id)
        return [(o.pk, str(o)) for o in qs]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(options__id=self.value())
        return queryset


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ['event', 'email', 'submitted_at', 'stato_pagamento', 'amount_paid', 'lezioni', 'bonifico']
    list_filter = ['payment_status', 'event', OptionFilter]
    search_fields = ['email', 'event__title', 'transfer_code']
    ordering = ['-submitted_at']
    fieldsets = [
        (None, {'fields': ['id', 'event', 'email', 'submitted_at', 'options']}),
        ('Pagamento', {'fields': ['payment_status', 'amount_paid', 'paypal_order_id']}),
        ('Bonifico', {
            'fields': ['transfer_code', 'causale', 'transfer_chosen_at', 'scadenza_bonifico',
                       'distinta', 'receipt_uploaded_at', 'transfer_note'],
            'description': "Controlla l'accredito (o la distinta), poi usa i pulsanti in fondo: "
                           '"Bonifico ricevuto" conferma l\'iscrizione e invia l\'email; '
                           '"Rifiuta distinta" invia all\'iscritto la nota qui sotto e gli chiede di ricaricarla.',
        }),
    ]
    readonly_fields = ['id', 'event', 'email', 'submitted_at', 'payment_status', 'paypal_order_id',
                       'amount_paid', 'options', 'transfer_code', 'causale', 'transfer_chosen_at',
                       'scadenza_bonifico', 'distinta', 'receipt_uploaded_at']
    inlines = [RegistrationAnswerInline]
    actions = ['mark_transfer_received', 'cancel_registrations', 'export_csv']
    change_form_template = 'admin/events/registration/transfer_change_form.html'

    # --- Distinta: scaricabile solo da qui, mai da un URL pubblico ---

    def get_urls(self):
        custom = [
            path('<uuid:registration_id>/distinta/',
                 self.admin_site.admin_view(self.receipt_view),
                 name='events_registration_receipt'),
        ]
        return custom + super().get_urls()

    def receipt_view(self, request, registration_id):
        registration = self.get_object(request, str(registration_id))
        if registration is None or not self.has_view_permission(request, registration):
            raise Http404
        if not registration.transfer_receipt:
            raise Http404
        ext = registration.transfer_receipt.name.rsplit('.', 1)[-1].lower()
        return FileResponse(
            registration.transfer_receipt.open('rb'),
            filename=f'distinta-{registration.transfer_code}.{ext}',
        )

    def distinta(self, obj):
        if not obj.transfer_receipt:
            return '-'
        url = reverse('admin:events_registration_receipt', args=[obj.pk])
        return format_html('<a href="{}" target="_blank" rel="noopener">Apri la distinta</a>', url)
    distinta.short_description = 'Distinta'

    def causale(self, obj):
        return obj.transfer_reference if obj.transfer_code else '-'
    causale.short_description = 'Causale attesa'

    def scadenza_bonifico(self, obj):
        deadline = obj.transfer_deadline
        if not deadline:
            return '-'
        text = timezone.localtime(deadline).strftime('%d/%m/%Y')
        if obj.transfer_overdue:
            return format_html('<strong class="transfer-overdue">{} (scaduto)</strong>', text)
        return text
    scadenza_bonifico.short_description = 'Scadenza bonifico'

    def bonifico(self, obj):
        if not obj.transfer_code:
            return '-'
        if obj.payment_status == 'transfer_review':
            return f'{obj.transfer_code} · distinta da verificare'
        if obj.transfer_overdue:
            return format_html('{} · <strong class="transfer-overdue">scaduto</strong>', obj.transfer_code)
        if obj.payment_status == 'transfer' and obj.transfer_chosen_at:
            days = (timezone.now() - obj.transfer_chosen_at).days
            return f'{obj.transfer_code} · in attesa da {days} g'
        return obj.transfer_code
    bonifico.short_description = 'Bonifico'

    # --- Azioni bonifico ---

    def _confirm_transfer(self, registration):
        registration.payment_status = 'completed'
        registration.transfer_note = ''
        registration.save(update_fields=['payment_status', 'transfer_note'])
        send_confirmation_email(registration)

    @admin.action(description='Bonifico ricevuto: conferma e invia email')
    def mark_transfer_received(self, request, queryset):
        done = 0
        for registration in queryset.filter(payment_status__in=['transfer', 'transfer_review']):
            self._confirm_transfer(registration)
            done += 1
        skipped = queryset.count() - done
        self.message_user(request, f'{done} iscrizioni confermate.', messages.SUCCESS)
        if skipped:
            self.message_user(request, f'{skipped} ignorate perché non in attesa di bonifico.', messages.WARNING)

    @admin.action(description='Annulla iscrizioni non pagate (libera il posto)')
    def cancel_registrations(self, request, queryset):
        n = queryset.exclude(payment_status__in=['completed', 'free', 'review']).update(payment_status='cancelled')
        self.message_user(
            request,
            f'{n} iscrizioni annullate. Quelle già pagate o gratuite non vengono toccate.',
            messages.SUCCESS,
        )

    def response_change(self, request, obj):
        if '_transfer_ok' in request.POST and obj.is_bank_transfer:
            self._confirm_transfer(obj)
            self.message_user(request, 'Bonifico confermato: email di conferma inviata.', messages.SUCCESS)
            return HttpResponseRedirect(request.path)
        if '_transfer_reject' in request.POST and obj.payment_status == 'transfer_review':
            obj.payment_status = 'transfer'
            obj.save(update_fields=['payment_status'])
            send_receipt_rejected(obj)
            self.message_user(request, "Distinta rifiutata: l'iscritto è stato avvisato via email.", messages.WARNING)
            return HttpResponseRedirect(request.path)
        return super().response_change(request, obj)

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('options')

    def lezioni(self, obj):
        options = list(obj.options.all())
        if not options:
            return '-'
        return ', '.join(f'{timezone.localtime(o.date):%d/%m} {o.title}' for o in options)
    lezioni.short_description = 'Lezioni'

    @admin.action(description='Esporta le iscrizioni selezionate in CSV (Excel)')
    def export_csv(self, request, queryset):
        queryset = queryset.select_related('event').prefetch_related('options', 'answers__field')
        labels = []
        for reg in queryset:
            for answer in reg.answers.all():
                label = answer.field.label if answer.field else '?'
                if label not in labels:
                    labels.append(label)

        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="iscrizioni.csv"'
        response.write('﻿')  # BOM: Excel apre correttamente gli accenti
        writer = csv.writer(response, delimiter=';')
        writer.writerow(['Evento', 'Data iscrizione', 'Email', 'Stato pagamento',
                         'Importo (EUR)', 'Codice bonifico', 'Lezioni'] + labels)
        for reg in queryset:
            answers = {}
            for answer in reg.answers.all():
                label = answer.field.label if answer.field else '?'
                answers[label] = answer.value or (answer.file.name if answer.file else '')
            writer.writerow([
                reg.event.title,
                timezone.localtime(reg.submitted_at).strftime('%d/%m/%Y %H:%M'),
                reg.email,
                reg.get_payment_status_display(),
                str(reg.amount_paid).replace('.', ','),
                reg.transfer_code,
                self.lezioni(reg),
            ] + [answers.get(label, '') for label in labels])
        return response

    def stato_pagamento(self, obj):
        colors = {
            'free':      '#198754',
            'completed': '#198754',
            'pending':   '#fd7e14',
            'review':    '#0d6efd',
            'transfer':  '#fd7e14',
            'transfer_review': '#6f42c1',
            'failed':    '#dc3545',
            'cancelled': '#6c757d',
        }
        color = colors.get(obj.payment_status, '#6c757d')
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;'
            'border-radius:4px;font-size:0.85em">{}</span>',
            color, obj.get_payment_status_display()
        )
    stato_pagamento.short_description = 'Pagamento'

    def has_add_permission(self, request):
        return False


@admin.register(BankTransferSettings)
class BankTransferSettingsAdmin(admin.ModelAdmin):
    """Scheda unica: la lista porta direttamente al modulo di modifica."""
    fields = ['beneficiary', 'iban', 'bank_name', 'hold_days', 'min_days_before',
              'notify_email', 'instructions']
    search_fields = ['beneficiary', 'iban']
    list_filter = []
    ordering = ['pk']

    def changelist_view(self, request, extra_context=None):
        obj = BankTransferSettings.load()
        return HttpResponseRedirect(reverse('admin:events_banktransfersettings_change', args=[obj.pk]))

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
