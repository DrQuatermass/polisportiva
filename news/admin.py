from urllib.parse import urlencode, urljoin

from django.conf import settings
from django import forms
from django.contrib import admin
from django.utils.html import format_html
from ckeditor.widgets import CKEditorWidget

from .models import News, NewsImage


class NewsAdminForm(forms.ModelForm):
    class Meta:
        model = News
        fields = '__all__'
        widgets = {
            'content': CKEditorWidget(),
        }


class NewsImageInline(admin.TabularInline):
    model = NewsImage
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


@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    form = NewsAdminForm
    list_display = ['title', 'created_at', 'published', 'facebook_share']
    list_filter = ['published', 'created_at']
    search_fields = ['title', 'content', 'meta_description']
    ordering = ['-created_at']
    prepopulated_fields = {'slug': ('title',)}
    list_editable = ['published']
    inlines = [NewsImageInline]

    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'content', 'image', 'published', 'created_at'),
        }),
        ('SEO & Social', {
            'fields': ('meta_description', 'og_image'),
            'classes': ('collapse',),
            'description': 'Personalizza come appare la notizia su Google, Facebook e WhatsApp.',
        }),
    )

    def facebook_share(self, obj):
        site = getattr(settings, 'SITE_URL', '').rstrip('/\\')
        page_url = getattr(settings, 'FACEBOOK_PAGE_URL', 'https://www.facebook.com/')
        url = urljoin(f'{site}/', obj.get_absolute_url().lstrip('/'))
        share_url = f'https://www.facebook.com/share.php?{urlencode({"u": url, "display": "popup"})}'
        return format_html(
            '<div style="display:flex;gap:6px;align-items:center;white-space:nowrap;">'
            '<button type="button" data-url="{}" onclick="navigator.clipboard.writeText(this.dataset.url);this.textContent=\'Copiato\';" '
            'style="border:0;background:#198754;color:#fff;padding:4px 10px;border-radius:5px;font-size:0.82em;font-weight:600;cursor:pointer;">'
            'Copia link</button>'
            '<a href="{}" target="_blank" rel="noopener" '
            'style="display:inline-flex;align-items:center;background:#6c757d;color:#fff;padding:4px 10px;border-radius:5px;'
            'text-decoration:none;font-size:0.82em;font-weight:600;">Apri</a>'
            '<a href="{}" target="_blank" rel="noopener" '
            'style="display:inline-flex;align-items:center;background:#0d6efd;color:#fff;padding:4px 10px;border-radius:5px;'
            'text-decoration:none;font-size:0.82em;font-weight:600;">Pagina</a>'
            '<a href="{}" target="_blank" rel="noopener" '
            'style="display:inline-flex;align-items:center;background:#1877F2;color:#fff;padding:4px 10px;border-radius:5px;'
            'text-decoration:none;font-size:0.82em;font-weight:600;">Facebook</a>'
            '</div>',
            url,
            url,
            page_url,
            share_url,
        )
    facebook_share.short_description = 'Facebook'
    facebook_share.allow_tags = True
