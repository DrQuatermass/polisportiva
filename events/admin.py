from urllib.parse import urlencode, urljoin

from django.conf import settings
from django import forms
from django.contrib import admin
from django.utils.html import format_html
from ckeditor.widgets import CKEditorWidget

from .models import Event, EventImage, Registration, RegistrationAnswer, RegistrationField


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
    inlines = [EventImageInline, RegistrationFieldInline]

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
                'registration_notes',
            ],
            'classes': ['collapse'],
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
        url = urljoin(f'{site}/', obj.get_absolute_url().lstrip('/'))
        share_url = f'https://www.facebook.com/sharer/sharer.php?{urlencode({"u": url})}'
        return format_html(
            '<a href="{}" target="_blank" rel="noopener" '
            'style="display:inline-flex;align-items:center;gap:6px;'
            'background:#1877F2;color:#fff;padding:4px 12px;border-radius:5px;'
            'text-decoration:none;font-size:0.82em;font-weight:600;">'
            '<svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" fill="currentColor" viewBox="0 0 16 16">'
            '<path d="M16 8.049c0-4.446-3.582-8.05-8-8.05C3.58 0-.002 3.603-.002 8.05c0 4.017 2.926 7.347 6.75 7.951v-5.625h-2.03V8.05H6.75V6.275c0-2.017 1.195-3.131 3.022-3.131.876 0 1.791.157 1.791.157v1.98h-1.009c-.993 0-1.303.621-1.303 1.258v1.51h2.218l-.354 2.326H9.25V16c3.824-.604 6.75-3.934 6.75-7.951z"/>'
            '</svg>Condividi</a>',
            share_url
        )
    facebook_share.short_description = 'Facebook'
    facebook_share.allow_tags = True


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ['event', 'email', 'submitted_at', 'stato_pagamento', 'amount_paid']
    list_filter = ['payment_status', 'event']
    search_fields = ['email', 'event__title']
    ordering = ['-submitted_at']
    readonly_fields = ['id', 'event', 'email', 'submitted_at',
                       'payment_status', 'paypal_order_id', 'amount_paid']
    inlines = [RegistrationAnswerInline]

    def stato_pagamento(self, obj):
        colors = {
            'free':      '#198754',
            'completed': '#198754',
            'pending':   '#fd7e14',
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
