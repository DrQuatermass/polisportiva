from django.core.validators import FileExtensionValidator
from django.db import models


class Sponsor(models.Model):
    name = models.CharField(max_length=200, verbose_name='Nome')
    logo = models.FileField(
        upload_to='sponsors/',
        verbose_name='Logo',
        validators=[
            FileExtensionValidator(allowed_extensions=['svg', 'png', 'jpg', 'jpeg', 'webp']),
        ],
    )
    website = models.URLField(verbose_name='Sito web', blank=True)
    order = models.PositiveSmallIntegerField(default=0, verbose_name='Ordine')
    active = models.BooleanField(default=True, verbose_name='Attivo')

    class Meta:
        ordering = ['order', 'name']
        verbose_name = 'Sponsor'
        verbose_name_plural = 'Sponsor'

    def __str__(self):
        return self.name
