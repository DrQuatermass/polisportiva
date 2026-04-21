from django.contrib.admin.sites import AdminSite
from django.test import SimpleTestCase, override_settings
from django.urls import reverse

from .admin import NewsAdmin
from .models import News


class NewsAdminFacebookShareTests(SimpleTestCase):
    @override_settings(
        SITE_URL='https://example.test\\',
        FACEBOOK_PAGE_URL='https://www.facebook.com/profile.php?id=100057579972656',
    )
    def test_facebook_share_uses_encoded_url_parameter(self):
        admin = NewsAdmin(News, AdminSite())
        news = News(title='Dove si corre', slug='dove-si-corre')

        html = str(admin.facebook_share(news))

        self.assertIn(f'https://example.test{reverse("news_detail", kwargs={"slug": news.slug})}', html)
        self.assertIn('Copia link', html)
        self.assertIn('Pagina', html)
        self.assertIn(
            'https://www.facebook.com/profile.php?id=100057579972656',
            html,
        )
        self.assertNotIn('Apri', html)
        self.assertNotIn('Facebook', html)
        self.assertNotIn('share.php', html)
        self.assertNotIn('%5C', html)
