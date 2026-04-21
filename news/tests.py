from django.contrib.admin.sites import AdminSite
from django.test import SimpleTestCase, override_settings

from .admin import NewsAdmin
from .models import News


class NewsAdminFacebookShareTests(SimpleTestCase):
    @override_settings(SITE_URL='https://example.test\\')
    def test_facebook_share_uses_href_parameter(self):
        admin = NewsAdmin(News, AdminSite())
        news = News(title='Dove si corre', slug='dove-si-corre')

        html = str(admin.facebook_share(news))

        self.assertIn(
            'https://www.facebook.com/sharer/sharer.php?href='
            'https%3A%2F%2Fexample.test%2Fnews%2Fdove-si-corre%2F',
            html,
        )
        self.assertNotIn('sharer.php?u=', html)
        self.assertNotIn('%5C', html)
