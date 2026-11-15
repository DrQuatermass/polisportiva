import csv
from urllib.parse import urljoin

from django.conf import settings
from django import forms
from django.contrib import admin
from django.http import HttpResponse
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html
from ckeditor.widgets import CKEditorWidget

from .models import (
    Event, EventImage, EventOption, Registration, RegistrationAnswer, RegistrationField,
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
    list_display = ['event', 'email', 'submitted_at', 'stato_pagamento', 'amount_paid', 'lezioni']
    list_filter = ['payment_status', 'event', OptionFilter]
    search_fields = ['email', 'event__title']
    ordering = ['-submitted_at']
    readonly_fields = ['id', 'event', 'email', 'submitted_at',
                       'payment_status', 'paypal_order_id', 'amount_paid', 'options']
    inlines = [RegistrationAnswerInline]
    actions = ['export_csv']

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
                         'Importo (EUR)', 'Lezioni'] + labels)
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
                self.lezioni(reg),
            ] + [answers.get(label, '') for label in labels])
        return response

    def stato_pagamento(self, obj):
        colors = {
            'free':      '#198754',
            'completed': '#198754',
            'pending':   '#fd7e14',
            'review':    '#0d6efd',
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
