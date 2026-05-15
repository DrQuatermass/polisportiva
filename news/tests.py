from django.contrib.admin.sites import AdminSite
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .admin import NewsAdmin
from .models import News


class NewsAdminFacebookShareTests(SimpleTestCase):
    @override_settings(
        SITE_URL='https://example.test\\',
        FACEBOOK_PAGE_URL='https://www.facebook.com/psmcyclingteam',
    )
    def test_facebook_share_uses_encoded_url_parameter(self):
        admin = NewsAdmin(News, AdminSite())
        news = News(title='Dove si corre', slug='dove-si-corre')

        html = str(admin.facebook_share(news))

        self.assertIn(f'https://example.test{reverse("news_detail", kwargs={"slug": news.slug})}', html)
        self.assertIn('Copia link', html)
        self.assertIn('Pagina', html)
        self.assertIn(
            'https://www.facebook.com/psmcyclingteam',
            html,
        )
        self.assertNotIn('Apri', html)
        self.assertNotIn('Facebook', html)
        self.assertNotIn('share.php', html)
        self.assertNotIn('%5C', html)


class NewsSeoTests(TestCase):
    @override_settings(SITE_URL='https://polisportivasanmarinese.it')
    def test_detail_has_public_social_metadata_with_share_image(self):
        news = News.objects.create(
            title='Dove si corre',
            slug='dove-si-corre',
            content='Una notizia con una descrizione abbastanza chiara per Google e social.',
            created_at=timezone.now(),
            published=True,
        )

        response = self.client.get(reverse('news_detail', kwargs={'slug': news.slug}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'property="og:type" content="article"')
        self.assertContains(response, f'property="og:url" content="https://polisportivasanmarinese.it{news.get_absolute_url()}"')
        social_image_url = f'https://polisportivasanmarinese.it{reverse("news_social_image", kwargs={"slug": news.slug})}?v={int(news.created_at.timestamp())}'
        self.assertContains(response, f'property="og:image" content="{social_image_url}"')
        self.assertContains(response, f'property="og:image:url" content="{social_image_url}"')
        self.assertContains(response, f'rel="image_src" href="{social_image_url}"')
        self.assertContains(response, f'name="twitter:image:alt" content="{news.title}"')
        self.assertContains(response, 'property="og:image:type" content="image/jpeg"')
        self.assertContains(response, 'name="robots" content="index,follow,max-image-preview:large"')

    def test_meta_description_fallback_removes_raw_urls(self):
        news = News(
            title='Dove si corre',
            slug='dove-si-corre-url',
            content='Un aggiornamento importante. https://example.test/articolo altri dettagli.',
            published=True,
        )

        description = news.get_meta_description()

        self.assertIn('Un aggiornamento importante.', description)
        self.assertIn('altri dettagli.', description)
        self.assertNotIn('https://example.test', description)

    def test_manual_meta_description_removes_raw_urls(self):
        news = News(
            title='Dove si corre',
            slug='dove-si-corre-url',
            content='Un aggiornamento importante per la comunita.',
            meta_description='https://example.test/articolo',
            published=True,
        )

        description = news.get_meta_description()

        self.assertEqual(description, 'Un aggiornamento importante per la comunita.')

    def test_unpublished_news_is_hidden_from_detail_and_social_image(self):
        news = News.objects.create(
            title='Bozza',
            slug='bozza',
            content='Contenuto non pubblico',
            published=False,
        )

        detail_response = self.client.get(reverse('news_detail', kwargs={'slug': news.slug}))
        image_response = self.client.get(reverse('news_social_image', kwargs={'slug': news.slug}))

        self.assertEqual(detail_response.status_code, 404)
        self.assertEqual(image_response.status_code, 404)

    def test_social_image_endpoint_returns_jpeg_for_facebook(self):
        news = News.objects.create(
            title='Dove si corre',
            slug='dove-si-corre-social',
            content='Contenuto pubblico',
            published=True,
        )

        response = self.client.get(reverse('news_social_image', kwargs={'slug': news.slug}))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'image/jpeg')
        self.assertEqual(response.content[:3], b'\xff\xd8\xff')
        self.assertIn('public', response['Cache-Control'])
