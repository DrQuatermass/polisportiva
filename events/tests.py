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


class BankTransferTests(TestCase):
    """Pagamento con bonifico e caricamento distinta."""

    def setUp(self):
        import shutil
        import tempfile
        from decimal import Decimal
        from .models import BankTransferSettings, EventOption, Registration

        self.private_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.private_dir, ignore_errors=True)
        override = override_settings(PRIVATE_MEDIA_ROOT=self.private_dir, CONTACT_EMAIL='admin@example.test')
        override.enable()
        self.addCleanup(override.disable)

        bank = BankTransferSettings.load()
        bank.beneficiary = 'Polisportiva Sanmarinese'
        bank.iban = 'it60 x054 2811 1010 0000 0123 456'
        bank.save()

        now = timezone.now()
        self.event = Event.objects.create(
            title='Corso di cucina', slug='corso-cucina', description='Corso',
            date=now + timedelta(days=10), location='Carpi', published=True,
            registration_enabled=True, accept_bank_transfer=True,
        )
        self.option = EventOption.objects.create(
            event=self.event, title='Tortellini', price=Decimal('25'),
            date=now + timedelta(days=10), max_participants=1,
        )
        self.reg = Registration.objects.create(
            event=self.event, email='mario@example.test', payment_status='pending',
            amount_paid=Decimal('25'),
        )
        self.reg.options.set([self.option])

    def _choose(self):
        return self.client.post(reverse('choose_bank_transfer', args=[self.reg.id]))

    def _pdf(self, name='distinta.pdf', content=b'%PDF-1.4 test'):
        from django.core.files.uploadedfile import SimpleUploadedFile
        return SimpleUploadedFile(name, content, content_type='application/pdf')

    def test_iban_is_normalised(self):
        from .models import BankTransferSettings
        bank = BankTransferSettings.load()
        self.assertEqual(bank.iban, 'IT60X0542811101000000123456')
        self.assertEqual(bank.iban_display, 'IT60 X054 2811 1010 0000 0123 456')

    def test_payment_page_offers_transfer(self):
        response = self.client.get(reverse('event_payment', args=[self.reg.id]))
        self.assertContains(response, 'Pago con bonifico')

    def test_transfer_hidden_when_event_does_not_accept_it(self):
        self.event.accept_bank_transfer = False
        self.event.save()
        response = self.client.get(reverse('event_payment', args=[self.reg.id]))
        self.assertNotContains(response, 'Pago con bonifico')
        self._choose()
        self.reg.refresh_from_db()
        self.assertEqual(self.reg.payment_status, 'pending')

    def test_transfer_hidden_when_start_is_too_close(self):
        self.option.date = timezone.now() + timedelta(days=1)
        self.option.save()
        self.assertFalse(self.reg.bank_transfer_allowed())

    def test_choose_transfer_holds_seat_and_emails_instructions(self):
        from django.core import mail
        response = self._choose()
        self.assertRedirects(response, reverse('event_payment', args=[self.reg.id]), fetch_redirect_response=False)
        self.reg.refresh_from_db()
        self.assertEqual(self.reg.payment_status, 'transfer')
        self.assertEqual(len(self.reg.transfer_code), 6)
        self.assertTrue(self.option.is_full)  # il posto è riservato
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('IT60 X054', mail.outbox[0].body)
        self.assertIn(self.reg.transfer_reference, mail.outbox[0].body)

        page = self.client.get(reverse('event_payment', args=[self.reg.id]))
        self.assertContains(page, 'IT60 X054 2811')
        self.assertContains(page, 'Carica la distinta')

    def test_upload_receipt_is_private_and_alerts_admin(self):
        import os
        from django.core import mail
        self._choose()
        mail.outbox.clear()
        response = self.client.post(
            reverse('upload_transfer_receipt', args=[self.reg.id]), {'distinta': self._pdf()},
        )
        self.assertRedirects(
            response, reverse('event_payment', args=[self.reg.id]) + '?distinta=1',
            fetch_redirect_response=False,
        )
        self.reg.refresh_from_db()
        self.assertEqual(self.reg.payment_status, 'transfer_review')
        path = self.reg.transfer_receipt.path
        self.assertTrue(path.startswith(os.path.abspath(self.private_dir)))
        self.assertNotIn('distinta.pdf', path)  # nome casuale
        with self.assertRaises(ValueError):
            self.reg.transfer_receipt.url
        self.assertEqual(mail.outbox[0].to, ['admin@example.test'])

    def test_upload_rejects_fake_or_wrong_files(self):
        self._choose()
        url = reverse('upload_transfer_receipt', args=[self.reg.id])
        fake = self._pdf(content=b'MZ not a pdf')
        response = self.client.post(url, {'distinta': fake})
        self.assertContains(response, 'Formato non valido')
        exe = self._pdf(name='virus.exe', content=b'%PDF')
        response = self.client.post(url, {'distinta': exe})
        self.assertContains(response, 'Formato non valido')
        self.reg.refresh_from_db()
        self.assertEqual(self.reg.payment_status, 'transfer')

    def test_upload_not_allowed_before_choosing_transfer(self):
        response = self.client.post(
            reverse('upload_transfer_receipt', args=[self.reg.id]), {'distinta': self._pdf()},
        )
        self.assertEqual(response.status_code, 404)

    def _admin_client(self):
        from django.contrib.auth import get_user_model
        user = get_user_model().objects.create_superuser('admin', 'a@example.test', 'pw')
        self.client.force_login(user)

    def test_admin_receipt_download_requires_login(self):
        self._choose()
        self.client.post(reverse('upload_transfer_receipt', args=[self.reg.id]), {'distinta': self._pdf()})
        url = reverse('admin:events_registration_receipt', args=[self.reg.id])
        self.assertEqual(self.client.get(url).status_code, 302)  # verso il login
        self._admin_client()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(b''.join(response.streaming_content), b'%PDF-1.4 test')

    def test_admin_confirm_button_completes_and_emails(self):
        from django.core import mail
        self._choose()
        self._admin_client()
        mail.outbox.clear()
        url = reverse('admin:events_registration_change', args=[self.reg.id])
        page = self.client.get(url)
        self.assertContains(page, 'Bonifico ricevuto')
        self.client.post(url, {
            'transfer_note': '', '_transfer_ok': '1',
            'answers-TOTAL_FORMS': '0', 'answers-INITIAL_FORMS': '0',
        })
        self.reg.refresh_from_db()
        self.assertEqual(self.reg.payment_status, 'completed')
        self.assertEqual(mail.outbox[0].subject, 'Conferma iscrizione: Corso di cucina')

    def test_admin_reject_sends_note_and_allows_reupload(self):
        from django.core import mail
        self._choose()
        self.client.post(reverse('upload_transfer_receipt', args=[self.reg.id]), {'distinta': self._pdf()})
        self._admin_client()
        mail.outbox.clear()
        url = reverse('admin:events_registration_change', args=[self.reg.id])
        self.client.post(url, {
            'transfer_note': 'Importo diverso da quello dovuto', '_transfer_reject': '1',
            'answers-TOTAL_FORMS': '0', 'answers-INITIAL_FORMS': '0',
        })
        self.reg.refresh_from_db()
        self.assertEqual(self.reg.payment_status, 'transfer')
        self.assertIn('Importo diverso', mail.outbox[0].body)
        page = self.client.get(reverse('event_payment', args=[self.reg.id]))
        self.assertContains(page, 'non è stata accettata')

    def test_admin_bulk_action_and_cancel(self):
        from .admin import RegistrationAdmin
        from .models import Registration
        self._choose()
        admin = RegistrationAdmin(Registration, AdminSite())
        admin.message_user = lambda *a, **k: None
        admin.cancel_registrations(None, Registration.objects.all())
        self.reg.refresh_from_db()
        self.assertEqual(self.reg.payment_status, 'cancelled')
        self.assertFalse(self.option.is_full)  # posto liberato

    def test_bank_settings_admin_is_single_page(self):
        self._admin_client()
        response = self.client.get(reverse('admin:events_banktransfersettings_changelist'))
        self.assertRedirects(response, reverse('admin:events_banktransfersettings_change', args=[1]))

    def test_payment_page_is_never_cached(self):
        response = self.client.get(reverse('event_payment', args=[self.reg.id]))
        self.assertIn('no-store', response['Cache-Control'])


class PrivateAttachmentTests(TestCase):
    """Gli allegati del modulo di iscrizione non devono essere pubblici."""

    def setUp(self):
        import shutil
        import tempfile
        from .models import RegistrationField

        self.private_dir = tempfile.mkdtemp()
        self.media_dir = tempfile.mkdtemp()
        for d in (self.private_dir, self.media_dir):
            self.addCleanup(shutil.rmtree, d, ignore_errors=True)
        override = override_settings(PRIVATE_MEDIA_ROOT=self.private_dir, MEDIA_ROOT=self.media_dir)
        override.enable()
        self.addCleanup(override.disable)

        self.event = Event.objects.create(
            title='Gara', slug='gara', description='x', date=timezone.now() + timedelta(days=5),
            location='Carpi', published=True, registration_enabled=True,
        )
        self.field = RegistrationField.objects.create(
            event=self.event, field_type='file', label='Certificato medico', required=True,
        )
        self.url = reverse('event_register', args=[self.event.slug])

    def _upload(self, name='certificato.pdf', content=b'%PDF-1.4 cert'):
        from django.core.files.uploadedfile import SimpleUploadedFile
        return self.client.post(self.url, {
            'reg_email': 'a@example.test',
            f'field_{self.field.pk}': SimpleUploadedFile(name, content),
        })

    def test_attachment_saved_privately_with_random_name(self):
        import os
        from .models import RegistrationAnswer
        self._upload()
        answer = RegistrationAnswer.objects.get()
        self.assertTrue(answer.file.path.startswith(os.path.abspath(self.private_dir)))
        self.assertNotIn('certificato', answer.file.name)
        self.assertEqual(os.listdir(self.media_dir), [])
        with self.assertRaises(ValueError):
            answer.file.url

    def test_disallowed_extension_rejected(self):
        from .models import Registration
        response = self._upload(name='script.exe')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Registration.objects.exists())

    def test_admin_attachment_requires_login(self):
        from django.contrib.auth import get_user_model
        from .models import RegistrationAnswer
        self._upload()
        answer = RegistrationAnswer.objects.get()
        url = reverse('admin:events_registration_attachment', args=[answer.registration_id, answer.pk])
        self.assertEqual(self.client.get(url).status_code, 302)

        user = get_user_model().objects.create_superuser('admin', 'adm@example.test', 'pw')
        self.client.force_login(user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(b''.join(response.streaming_content), b'%PDF-1.4 cert')
        self.assertIn('certificato-medico-', response['Content-Disposition'])

        page = self.client.get(reverse('admin:events_registration_change', args=[answer.registration_id]))
        self.assertContains(page, 'Apri allegato')
        self.assertNotContains(page, answer.file.name)

    def test_attachment_of_other_registration_is_404(self):
        from django.contrib.auth import get_user_model
        from .models import Registration, RegistrationAnswer
        self._upload()
        answer = RegistrationAnswer.objects.get()
        other = Registration.objects.create(event=self.event, email='b@example.test')
        user = get_user_model().objects.create_superuser('admin', 'adm@example.test', 'pw')
        self.client.force_login(user)
        url = reverse('admin:events_registration_attachment', args=[other.pk, answer.pk])
        self.assertEqual(self.client.get(url).status_code, 404)


class OptionExtrasTests(TestCase):
    """Voci extra (es. tessera) tra le lezioni: si sommano, fuori dal pacchetto."""

    def setUp(self):
        from decimal import Decimal
        from .models import EventOption
        now = timezone.now()
        self.event = Event.objects.create(
            title='Corso', slug='corso-extra', description='x', date=now + timedelta(days=10),
            location='Carpi', published=True, registration_enabled=True, bundle_price=Decimal('120'),
        )
        self.lessons = [
            EventOption.objects.create(event=self.event, title=f'L{i}', price=Decimal(p),
                                       date=now + timedelta(days=10 + i), order=i)
            for i, p in enumerate([20, 20, 25, 20, 20, 20])
        ]
        self.card = EventOption.objects.create(
            event=self.event, title='Tessera ARCI 2026/27', price=Decimal('10'), is_extra=True, order=99,
        )
        self.url = reverse('event_register', args=[self.event.slug])

    def _post(self, options):
        return self.client.post(self.url, {'reg_email': 'a@example.test', 'reg_options': [o.pk for o in options]})

    def _amount(self):
        from .models import Registration
        return Registration.objects.latest('submitted_at').amount_paid

    def test_bundle_still_applies_with_card(self):
        self._post(self.lessons + [self.card])
        self.assertEqual(self._amount(), 130)

    def test_bundle_without_card(self):
        self._post(self.lessons)
        self.assertEqual(self._amount(), 120)

    def test_some_lessons_plus_card(self):
        self._post(self.lessons[:2] + [self.card])
        self.assertEqual(self._amount(), 50)

    def test_card_alone_is_rejected(self):
        from .models import Registration
        response = self._post([self.card])
        self.assertContains(response, 'Seleziona almeno una lezione')
        self.assertFalse(Registration.objects.exists())

    def test_extra_without_date_never_closes_and_bundle_ignores_it(self):
        self.assertFalse(self.card.is_closed)
        self.assertEqual(self.event.options_total_price, 125)
        self.assertEqual(len(self.event.lessons), 6)
        self.assertTrue(self.event.bundle_available)

    def test_lesson_requires_date(self):
        from django.core.exceptions import ValidationError
        from .models import EventOption
        with self.assertRaises(ValidationError):
            EventOption(event=self.event, title='Senza data', price=10).full_clean()

    def test_detail_shows_card_in_extras_section(self):
        response = self.client.get(reverse('event_detail', args=[self.event.slug]))
        self.assertContains(response, 'Da aggiungere')
        self.assertContains(response, 'data-extra', count=1)
        self.assertContains(response, 'Tutte e 6 le lezioni')

    def test_payment_page_marks_bundle_and_lists_card(self):
        from .models import Registration
        self._post(self.lessons + [self.card])
        reg = Registration.objects.get()
        page = self.client.get(reverse('event_payment', args=[reg.id]))
        self.assertContains(page, 'Prezzo pacchetto completo applicato')
        self.assertContains(page, 'Tessera ARCI 2026/27')
