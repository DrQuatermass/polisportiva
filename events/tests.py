from datetime import timedelta

from django.contrib.admin.sites import AdminSite
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .admin import EventAdmin
from .models import Event


class EventPublicationTests(TestCase):
    def test_published_event_without_registration_is_listed(self):
        event = Event.objects.create(
            title='Gara sociale',
            slug='gara-sociale',
            description='Evento visibile anche senza iscrizioni.',
            date=timezone.now() + timedelta(days=7),
            location='Carpi',
            published=True,
            registration_enabled=False,
        )

        response = self.client.get(reverse('events_list'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, event.title)

    def test_unpublished_event_is_hidden_from_list_and_detail(self):
        event = Event.objects.create(
            title='Evento interno',
            slug='evento-interno',
            description='Non deve comparire sul sito.',
            date=timezone.now() + timedelta(days=7),
            location='Carpi',
            published=False,
        )

        list_response = self.client.get(reverse('events_list'))
        detail_response = self.client.get(reverse('event_detail', args=[event.slug]))

        self.assertEqual(list_response.status_code, 200)
        self.assertNotContains(list_response, event.title)
        self.assertEqual(detail_response.status_code, 404)


class EventAdminFacebookShareTests(TestCase):
    @override_settings(
        SITE_URL='https://example.test\\',
        FACEBOOK_PAGE_URL='https://www.facebook.com/psmcyclingteam',
    )
    def test_facebook_share_uses_encoded_url_parameter(self):
        admin = EventAdmin(Event, AdminSite())
        event = Event(
            title='Granfondo',
            slug='granfondo',
            description='Evento',
            date=timezone.now(),
            location='Carpi',
        )

        html = str(admin.facebook_share(event))

        self.assertIn(f'https://example.test{reverse("event_detail", kwargs={"slug": event.slug})}', html)
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


class EventSeoTests(TestCase):
    @override_settings(SITE_URL='https://polisportivasanmarinese.it')
    def test_detail_has_public_social_metadata_with_share_image(self):
        event = Event.objects.create(
            title='Granfondo',
            slug='granfondo',
            description='Evento sportivo aperto alla comunita.',
            date=timezone.now() + timedelta(days=7),
            location='Carpi',
            published=True,
        )

        response = self.client.get(reverse('event_detail', kwargs={'slug': event.slug}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'property="og:type" content="article"')
        self.assertContains(response, f'property="og:url" content="https://polisportivasanmarinese.it{event.get_absolute_url()}"')
        social_image_url = f'https://polisportivasanmarinese.it{reverse("event_social_image", kwargs={"slug": event.slug})}?v={int(event.date.timestamp())}'
        self.assertContains(response, f'property="og:image" content="{social_image_url}"')
        self.assertContains(response, f'property="og:image:url" content="{social_image_url}"')
        self.assertContains(response, 'property="og:image:type" content="image/jpeg"')
        self.assertContains(response, 'name="robots" content="index,follow,max-image-preview:large"')

    def test_social_image_endpoint_returns_jpeg_for_facebook(self):
        event = Event.objects.create(
            title='Granfondo',
            slug='granfondo-social',
            description='Evento pubblico',
            date=timezone.now() + timedelta(days=7),
            location='Carpi',
            published=True,
        )

        response = self.client.get(reverse('event_social_image', kwargs={'slug': event.slug}))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'image/jpeg')
        self.assertEqual(response.content[:3], b'\xff\xd8\xff')
        self.assertIn('public', response['Cache-Control'])
