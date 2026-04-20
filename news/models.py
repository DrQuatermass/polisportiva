import re

from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.html import strip_tags

from config.image_utils import optimize_image_field


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

    def save(self, *args, **kwargs):
        optimize_image_field(self, 'image')
        optimize_image_field(self, 'og_image', max_size=(1200, 630))
        super().save(*args, **kwargs)

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


class NewsImage(models.Model):
    news = models.ForeignKey(News, on_delete=models.CASCADE, related_name='gallery_images')
    image = models.ImageField(upload_to='news/gallery/', verbose_name='Foto')
    caption = models.CharField(max_length=200, blank=True, verbose_name='Didascalia')
    order = models.PositiveIntegerField(default=0, verbose_name='Ordine')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Data caricamento')

    class Meta:
        ordering = ['order', 'id']
        verbose_name = 'Foto notizia'
        verbose_name_plural = 'Foto notizia'

    def __str__(self):
        return self.caption or f'Foto: {self.news}'

    def save(self, *args, **kwargs):
        optimize_image_field(self, 'image')
        super().save(*args, **kwargs)
