from django.conf import settings
from django import forms
from django.contrib import admin
from django.utils.html import format_html
from ckeditor.widgets import CKEditorWidget

from .models import News


class NewsAdminForm(forms.ModelForm):
    class Meta:
        model = News
        fields = '__all__'
        widgets = {
            'content': CKEditorWidget(),
        }


@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    form = NewsAdminForm
    list_display = ['title', 'created_at', 'published', 'facebook_share']
    list_filter = ['published', 'created_at']
    search_fields = ['title', 'content']
    ordering = ['-created_at']
    prepopulated_fields = {'slug': ('title',)}
    list_editable = ['published']

    def facebook_share(self, obj):
        site = getattr(settings, 'SITE_URL', '').rstrip('/')
        url = f'{site}/news/{obj.slug}/'
        share_url = f'https://www.facebook.com/sharer/sharer.php?u={url}'
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
