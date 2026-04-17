import re

from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.html import strip_tags


class News(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    content = models.TextField()
    image = models.ImageField(upload_to='news/', blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    published = models.BooleanField(default=False)

    # --- SEO ---
    meta_description = models.CharField(
        max_length=160,
        blank=True,
        verbose_name='Meta description',
        help_text='Testo mostrato da Google e social (max 160 caratteri). '
                  'Se vuoto viene generato dal contenuto.',
    )
    og_image = models.ImageField(
        upload_to='news/og/',
        blank=True,
        null=True,
        verbose_name='Immagine social (opzionale)',
        help_text='1200x630 consigliato. Se vuoto usa l\'immagine principale.',
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Notizia'
        verbose_name_plural = 'Notizie'

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('news_detail', kwargs={'slug': self.slug})

    def get_meta_description(self):
        if self.meta_description:
            return self.meta_description
        text = strip_tags(self.content or '')
        text = re.sub(r'\s+', ' ', text).strip()
        return text[:157] + '…' if len(text) > 160 else text

    def get_og_image_url(self):
        if self.og_image:
            return self.og_image.url
        if self.image:
            return self.image.url
        return ''
