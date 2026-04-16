from django.db import models
from django.utils import timezone


class News(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    content = models.TextField()
    image = models.ImageField(upload_to='news/', blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    published = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Notizia'
        verbose_name_plural = 'Notizie'

    def __str__(self):
        return self.title
