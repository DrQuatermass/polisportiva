from django.core.validators import FileExtensionValidator
from django.db import models


class Team(models.Model):
    name = models.CharField(max_length=200, verbose_name='Nome')
    slug = models.SlugField(unique=True)
    category = models.CharField(max_length=100, verbose_name='Categoria')
    description = models.TextField(verbose_name='Descrizione')
    image = models.ImageField(upload_to='teams/', blank=True, null=True, verbose_name='Immagine')
    regulation = models.FileField(
        upload_to='documents/',
        blank=True,
        null=True,
        verbose_name='Regolamento (PDF)',
        validators=[FileExtensionValidator(allowed_extensions=['pdf'])],
    )

    class Meta:
        ordering = ['category', 'name']
        verbose_name = 'Squadra'
        verbose_name_plural = 'Squadre'

    def __str__(self):
        return self.name
