from django.contrib import admin
from django.utils.html import format_html
from .models import Document


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'has_content_icon', 'has_file_icon', 'order', 'active')
    list_filter = ('category', 'active')
    search_fields = ('title', 'description', 'content')
    ordering = ('category', 'order', 'title')
    list_editable = ('order', 'active')
    prepopulated_fields = {'slug': ('title',)}

    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'category', 'order', 'active'),
        }),
        ('Contenuto', {
            'fields': ('description', 'content'),
            'description': 'Il <strong>Contenuto HTML</strong> viene mostrato direttamente nella pagina web. '
                           'Il <strong>File PDF</strong> e opzionale e aggiunge un pulsante di download.',
        }),
        ('File PDF', {
            'fields': ('file',),
        }),
        ('SEO', {
            'fields': ('meta_description',),
            'classes': ('collapse',),
        }),
    )

    def has_content_icon(self, obj):
        if obj.has_content:
            return format_html('<span style="color:{};">{}</span>', 'green', '✓')
        return format_html('<span style="color:{};">{}</span>', '#ccc', '—')
    has_content_icon.short_description = 'Contenuto'

    def has_file_icon(self, obj):
        if obj.has_file:
            return format_html('<span style="color:{};">{}</span>', 'green', '✓')
        return format_html('<span style="color:{};">{}</span>', '#ccc', '—')
    has_file_icon.short_description = 'PDF'
