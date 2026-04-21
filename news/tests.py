from django.contrib.admin.sites import AdminSite
from django.test import SimpleTestCase, override_settings
from django.urls import reverse

from .admin import NewsAdmin
from .models import News


class NewsAdminFacebookShareTests(SimpleTestCase):
    @override_settings(SITE_URL='https://example.test\\')
    def test_facebook_share_uses_encoded_url_parameter(self):
        admin = NewsAdmin(News, AdminSite())
        news = News(title='Dove si corre', slug='dove-si-corre')

        html = str(admin.facebook_share(news))

        self.assertIn(
            'https://www.facebook.com/share.php?u='
            f'https%3A%2F%2Fexample.test{reverse("news_detail", kwargs={"slug": news.slug}).replace("/", "%2F")}'
            '&amp;display=popup',
            html,
        )
        self.assertIn('Copia link', html)
        self.assertIn('Apri', html)
        self.assertNotIn('share.php?href=', html)
        self.assertNotIn('%5C', html)
