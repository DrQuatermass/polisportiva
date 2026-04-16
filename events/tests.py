from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

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
