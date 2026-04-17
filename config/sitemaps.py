from django.urls import reverse
from django.contrib.sitemaps import Sitemap

from documents.models import Document
from events.models import Event
from news.models import News


class StaticViewSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.7
    protocol = 'https'

    def items(self):
        return [
            'home',
            'chi_siamo',
            'ciclismo',
            'calendario',
            'sponsors_list',
            'documents_list',
            'events_list',
            'news_list',
            'contatti',
        ]

    def location(self, item):
        return reverse(item)


class NewsSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.6
    protocol = 'https'

    def items(self):
        return News.objects.filter(published=True)

    def lastmod(self, obj):
        return obj.created_at

    def location(self, obj):
        return reverse('news_detail', kwargs={'slug': obj.slug})


class EventSitemap(Sitemap):
    changefreq = 'daily'
    priority = 0.6
    protocol = 'https'

    def items(self):
        return Event.objects.filter(published=True)

    def lastmod(self, obj):
        return obj.date

    def location(self, obj):
        return reverse('event_detail', kwargs={'slug': obj.slug})


class DocumentSitemap(Sitemap):
    changefreq = 'monthly'
    priority = 0.5
    protocol = 'https'

    def items(self):
        return Document.objects.filter(active=True)

    def lastmod(self, obj):
        return obj.created_at
