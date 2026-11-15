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
        social_image_url = f'https://polisportivasanmarinese.it{reverse("event_social_image", kwargs={"slug": event.slug})}'
        self.assertContains(response, f'property="og:image" content="{social_image_url}"')
        self.assertContains(response, f'property="og:image:url" content="{social_image_url}"')
        self.assertContains(response, f'rel="image_src" href="{social_image_url}"')
        self.assertContains(response, f'name="twitter:image:alt" content="{event.title}"')
        self.assertContains(response, 'property="og:image:type" content="image/jpeg"')
        self.assertContains(response, 'name="robots" content="index,follow,max-image-preview:large"')

    def test_meta_description_fallback_removes_raw_urls(self):
        event = Event(
            title='Pastasciuttata',
            slug='pastasciuttata',
            description='Serata solidale &amp; conviviale. https://example.test/articolo dettagli utili.',
            date=timezone.now() + timedelta(days=7),
            location='Carpi',
        )

        description = event.get_meta_description()

        self.assertIn('Serata solidale & conviviale.', description)
        self.assertIn('dettagli utili.', description)
        self.assertNotIn('https://example.test', description)

    def test_manual_meta_description_removes_raw_urls(self):
        event = Event(
            title='Pastasciuttata',
            slug='pastasciuttata',
            description='Serata solidale con cena e raccolta fondi.',
            meta_description='https://example.test/articolo',
            date=timezone.now() + timedelta(days=7),
            location='Carpi',
        )

        description = event.get_meta_description()

        self.assertEqual(description, 'Serata solidale con cena e raccolta fondi.')

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


class EventOptionsTests(TestCase):
    """Eventi a lezioni selezionabili (es. corso di cucina) con prezzo pacchetto."""

    def setUp(self):
        from decimal import Decimal
        from .models import EventOption, RegistrationField
        now = timezone.now()
        self.event = Event.objects.create(
            title='Corso di cucina', slug='corso-cucina', description='Corso',
            date=now + timedelta(days=10), location='Carpi', published=True,
            registration_enabled=True, bundle_price=Decimal('120'),
        )
        prices = [20, 20, 25, 20, 20, 20]
        self.options = [
            EventOption.objects.create(
                event=self.event, title=f'Lezione {i + 1}', price=Decimal(p),
                date=now + timedelta(days=10 + 7 * i), order=i, max_participants=2,
            )
            for i, p in enumerate(prices)
        ]
        self.name_field = RegistrationField.objects.create(
            event=self.event, field_type='text', label='Nome', required=True,
        )
        self.url = reverse('event_register', args=[self.event.slug])

    def _post(self, options, email='a@example.test'):
        return self.client.post(self.url, {
            'reg_email': email,
            f'field_{self.name_field.pk}': 'Mario',
            'reg_options': [o.pk for o in options],
        })

    def _last_registration(self):
        from .models import Registration
        return Registration.objects.latest('submitted_at')

    def test_partial_selection_sums_prices(self):
        response = self._post(self.options[:3])
        reg = self._last_registration()
        self.assertRedirects(response, reverse('event_payment', args=[reg.id]), fetch_redirect_response=False)
        self.assertEqual(reg.amount_paid, 65)
        self.assertEqual(reg.payment_status, 'pending')
        self.assertEqual(set(reg.options.all()), set(self.options[:3]))

    def test_all_options_use_bundle_price(self):
        self._post(self.options)
        self.assertEqual(self._last_registration().amount_paid, 120)

    def test_bundle_never_exceeds_sum(self):
        from decimal import Decimal
        self.event.bundle_price = Decimal('500')
        self.event.save()
        self._post(self.options)
        self.assertEqual(self._last_registration().amount_paid, 125)

    def test_no_selection_is_rejected(self):
        from .models import Registration
        response = self._post([])
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Seleziona almeno una lezione')
        self.assertFalse(Registration.objects.exists())

    def test_full_option_is_rejected(self):
        from .models import Registration
        for email in ['x@example.test', 'y@example.test']:
            reg = Registration.objects.create(event=self.event, email=email, payment_status='completed')
            reg.options.set([self.options[0]])
        self.assertTrue(self.options[0].is_full)

        response = self._post([self.options[0], self.options[1]])
        self.assertContains(response, 'Non più disponibili')
        self.assertEqual(Registration.objects.count(), 2)

    def test_pending_registrations_do_not_take_seats(self):
        from .models import Registration
        for email in ['x@example.test', 'y@example.test']:
            reg = Registration.objects.create(event=self.event, email=email, payment_status='pending')
            reg.options.set([self.options[0]])
        self.assertFalse(self.options[0].is_full)

    def test_closed_option_is_rejected_and_disables_bundle(self):
        self.options[0].date = timezone.now() - timedelta(hours=1)
        self.options[0].save()
        self.assertFalse(self.event.bundle_available)
        response = self._post([self.options[0]])
        self.assertContains(response, 'Non più disponibili')

    def test_option_from_other_event_is_rejected(self):
        from .models import EventOption, Registration
        other = Event.objects.create(
            title='Altro', slug='altro', description='x', date=timezone.now() + timedelta(days=3),
            location='Carpi', published=True, registration_enabled=True,
        )
        foreign = EventOption.objects.create(
            event=other, title='Estranea', price=1, date=timezone.now() + timedelta(days=3),
        )
        self._post([foreign])
        self.assertFalse(Registration.objects.exists())

    def test_detail_renders_options_and_bundle(self):
        response = self.client.get(reverse('event_detail', args=[self.event.slug]))
        self.assertContains(response, 'class="event-option-input"', count=6)
        self.assertContains(response, 'data-bundle-price="120.00"')
        self.assertContains(response, 'Seleziona tutte')

    def test_free_options_skip_payment(self):
        from .models import Registration
        for o in self.options:
            o.price = 0
            o.save()
        self.event.bundle_price = None
        self.event.save()
        response = self._post(self.options[:1])
        reg = Registration.objects.get()
        self.assertEqual(reg.payment_status, 'free')
        self.assertRedirects(response, reverse('event_registration_confirm', args=[reg.id]), fetch_redirect_response=False)

    def test_admin_csv_export_lists_options(self):
        from .admin import RegistrationAdmin
        from .models import Registration
        self._post(self.options[:2])
        admin = RegistrationAdmin(Registration, AdminSite())
        response = admin.export_csv(None, Registration.objects.all())
        content = response.content.decode('utf-8-sig')
        self.assertIn('Lezione 1', content)
        self.assertIn('Lezione 2', content)
        self.assertIn('Mario', content)
        self.assertIn('40', content)
