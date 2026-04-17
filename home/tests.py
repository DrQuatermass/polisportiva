from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from documents.models import Document
from events.models import Event
from news.models import News


class SitemapTests(TestCase):
    @override_settings(ALLOWED_HOSTS=['polisportivasanmarinese.it'])
    def test_sitemap_lists_public_pages_and_published_content(self):
        News.objects.create(
            title='Notizia pubblica',
            slug='notizia-pubblica',
            content='Contenuto',
            published=True,
        )
        News.objects.create(
            title='Bozza',
            slug='bozza',
            content='Contenuto',
            published=False,
        )
        Event.objects.create(
            title='Evento pubblico',
            slug='evento-pubblico',
            description='Descrizione',
            date=timezone.now(),
            location='Carpi',
            published=True,
        )
        Document.objects.create(
            title='Documento pubblico',
            slug='documento-pubblico',
            category='privacy',
            active=True,
        )

        response = self.client.get('/sitemap.xml', HTTP_HOST='polisportivasanmarinese.it', secure=True)

        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn('https://polisportivasanmarinese.it/', content)
        self.assertIn(f'https://polisportivasanmarinese.it{reverse("news_detail", kwargs={"slug": "notizia-pubblica"})}', content)
        self.assertIn(f'https://polisportivasanmarinese.it{reverse("event_detail", kwargs={"slug": "evento-pubblico"})}', content)
        self.assertIn(f'https://polisportivasanmarinese.it{reverse("document_detail", kwargs={"slug": "documento-pubblico"})}', content)
        self.assertNotIn('bozza', content)
