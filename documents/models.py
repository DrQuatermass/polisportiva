import re

from django.core.validators import FileExtensionValidator
from django.db import models
from django.urls import reverse
from django.utils.html import strip_tags
from django.utils.text import slugify


class Document(models.Model):
    CATEGORY_CHOICES = [
        ('regolamento', 'Regolamenti'),
        ('etico', 'Codice Etico & Carta Etica'),
        ('safeguarding', 'Safeguarding'),
        ('privacy', 'Privacy & GDPR'),
        ('promo', 'Materiale promozionale'),
    ]

    title = models.CharField(max_length=200, verbose_name='Titolo')
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    category = models.CharField(
        max_length=30,
        choices=CATEGORY_CHOICES,
        verbose_name='Categoria',
    )
    description = models.TextField(blank=True, verbose_name='Descrizione breve')
    content = models.TextField(
        blank=True,
        verbose_name='Contenuto HTML',
        help_text='Incolla qui il testo del documento. Puoi usare semplici tag HTML come &lt;p&gt;, &lt;h3&gt;, &lt;ul&gt;, &lt;li&gt;, &lt;strong&gt;.',
    )
    file = models.FileField(
        upload_to='documents/',
        blank=True,
        null=True,
        verbose_name='File PDF (opzionale)',
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx'])],
    )
    order = models.PositiveSmallIntegerField(default=0, verbose_name='Ordine')
    active = models.BooleanField(default=True, verbose_name='Attivo')
    created_at = models.DateTimeField(auto_now_add=True)

    # --- SEO ---
    meta_description = models.CharField(
        max_length=160,
        blank=True,
        verbose_name='Meta description',
        help_text='Testo mostrato da Google (max 160 caratteri). '
                  'Se vuoto viene generato da descrizione/contenuto.',
    )

    class Meta:
        ordering = ['category', 'order', 'title']
        verbose_name = 'Documento'
        verbose_name_plural = 'Documenti'

    def __str__(self):
        return f'{self.get_category_display()} - {self.title}'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('document_detail', kwargs={'slug': self.slug})

    @property
    def has_content(self):
        return bool(self.content.strip())

    @property
    def has_file(self):
        return bool(self.file)

    def get_meta_description(self):
        if self.meta_description:
            return self.meta_description
        source = self.description or strip_tags(self.content or '')
        source = re.sub(r'\s+', ' ', source).strip()
        return source[:157] + '…' if len(source) > 160 else source
