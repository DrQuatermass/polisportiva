from datetime import date
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from documents.models import Document
from events.models import Event
from news.models import News
from home.views import CalendarioView


class _FakeIcsResponse:
    def __init__(self, content):
        self.content = content

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self):
        return self.content.encode()


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


class SiteContextProcessorTests(TestCase):
    @override_settings(SITE_URL='https://polisportivasanmarinese.it\\')
    def test_site_url_strips_forward_and_backslashes(self):
        response = self.client.get(reverse('home'))

        self.assertEqual(response.context['SITE_URL'], 'https://polisportivasanmarinese.it')


class CalendarioViewTests(TestCase):
    def _occupied_from_ics(self, ics):
        with patch('home.views.urlopen', return_value=_FakeIcsResponse(ics)):
            return CalendarioView()._fetch_occupied_by_day()

    @override_settings(GOOGLE_CALENDAR_ICS_URL='https://example.test/calendar.ics')
    def test_timed_multi_day_event_occupies_each_day(self):
        occupied_by_day = self._occupied_from_ics(
            """BEGIN:VCALENDAR
BEGIN:VEVENT
DTSTART:20260420T180000
DTEND:20260422T100000
SUMMARY:Saletta stage
END:VEVENT
END:VCALENDAR
"""
        )

        self.assertIn(date(2026, 4, 20), occupied_by_day)
        self.assertIn(date(2026, 4, 21), occupied_by_day)
        self.assertIn(date(2026, 4, 22), occupied_by_day)
        self.assertEqual(occupied_by_day[date(2026, 4, 20)][0]['time'], 'Dalle 18:00')
        self.assertEqual(occupied_by_day[date(2026, 4, 21)][0]['time'], 'Tutto il giorno')
        self.assertEqual(occupied_by_day[date(2026, 4, 22)][0]['time'], 'Fino alle 10:00')

    @override_settings(GOOGLE_CALENDAR_ICS_URL='https://example.test/calendar.ics')
    def test_timed_multi_day_event_ending_at_midnight_excludes_end_day(self):
        occupied_by_day = self._occupied_from_ics(
            """BEGIN:VCALENDAR
BEGIN:VEVENT
DTSTART:20260420T180000
DTEND:20260422T000000
SUMMARY:Palestra torneo
END:VEVENT
END:VCALENDAR
"""
        )

        self.assertIn(date(2026, 4, 20), occupied_by_day)
        self.assertIn(date(2026, 4, 21), occupied_by_day)
        self.assertNotIn(date(2026, 4, 22), occupied_by_day)

    @override_settings(GOOGLE_CALENDAR_ICS_URL='https://example.test/calendar.ics')
    def test_same_time_slots_are_merged_with_unique_rooms(self):
        occupied_by_day = self._occupied_from_ics(
            """BEGIN:VCALENDAR
BEGIN:VEVENT
DTSTART:20260420T180000
DTEND:20260420T200000
SUMMARY:Palestra allenamento
END:VEVENT
BEGIN:VEVENT
DTSTART:20260420T180000
DTEND:20260420T200000
SUMMARY:Saletta riunione
END:VEVENT
BEGIN:VEVENT
DTSTART:20260420T180000
DTEND:20260420T200000
SUMMARY:Palestra allenamento duplicato
END:VEVENT
END:VCALENDAR
"""
        )

        slots = occupied_by_day[date(2026, 4, 20)]

        self.assertEqual(len(slots), 1)
        self.assertEqual(slots[0]['time'], '18:00 - 20:00')
        self.assertEqual(
            [room['key'] for room in slots[0]['rooms']],
            ['palestra', 'saletta'],
        )
