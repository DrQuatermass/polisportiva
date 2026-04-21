from django.contrib.admin.sites import AdminSite
from django.test import SimpleTestCase, override_settings

from .admin import NewsAdmin
from .models import News


class NewsAdminFacebookShareTests(SimpleTestCase):
    @override_settings(SITE_URL='https://example.test\\')
    def test_facebook_share_uses_encoded_url_parameter(self):
        admin = NewsAdmin(News, AdminSite())
        news = News(title='Dove si corre', slug='dove-si-corre')

        html = str(admin.facebook_share(news))

        self.assertIn(
            'https://www.facebook.com/sharer/sharer.php?u='
            'https%3A%2F%2Fexample.test%2Fnews%2Fdove-si-corre%2F',
            html,
        )
        self.assertNotIn('sharer.php?href=', html)
        self.assertNotIn('%5C', html)
