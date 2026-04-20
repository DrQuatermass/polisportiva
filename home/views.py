import calendar
import logging
from collections import defaultdict
from datetime import date, datetime, timedelta
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.http import HttpResponse
from django.views.generic import FormView, TemplateView
from django.views.decorators.cache import never_cache

from events.models import Event
from news.models import News

from .forms import ContattoForm

logger = logging.getLogger(__name__)


class HomeView(TemplateView):
    template_name = 'home/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['latest_news'] = News.objects.filter(published=True)[:3]
        context['upcoming_events'] = Event.objects.filter(published=True, date__gte=timezone.now())[:3]
        return context


class ChiSiamoView(TemplateView):
    template_name = 'home/chi_siamo.html'


class CalendarioView(TemplateView):
    template_name = 'home/calendario.html'

    CALENDAR_ICS_URL = (
        'https://calendar.google.com/calendar/ical/'
        'polisportivasanmarinese%40gmail.com/public/basic.ics'
    )

    MONTH_NAMES = [
        'Gennaio', 'Febbraio', 'Marzo', 'Aprile', 'Maggio', 'Giugno',
        'Luglio', 'Agosto', 'Settembre', 'Ottobre', 'Novembre', 'Dicembre',
    ]

    WEEKDAY_LABELS = ['Lun', 'Mar', 'Mer', 'Gio', 'Ven', 'Sab', 'Dom']

    ROOM_TYPES = [
        ('palestra', 'Palestra'),
        ('saletta', 'Saletta'),
        ('salone', 'Salone'),
        ('campo-basket', 'Campo Basket'),
        ('parco', 'Parco'),
    ]

    RRULE_WEEKDAYS = {
        'MO': 0,
        'TU': 1,
        'WE': 2,
        'TH': 3,
        'FR': 4,
        'SA': 5,
        'SU': 6,
    }

    @method_decorator(never_cache)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    @staticmethod
    def _parse_ics_datetime(raw_value):
        italy_tz = ZoneInfo('Europe/Rome')
        value = raw_value.strip()

        if len(value) == 8:
            day = datetime.strptime(value, '%Y%m%d').date()
            return day, True

        if value.endswith('Z'):
            parsed = datetime.strptime(value, '%Y%m%dT%H%M%SZ').replace(tzinfo=ZoneInfo('UTC'))
            parsed = parsed.astimezone(italy_tz)
        else:
            fmt = '%Y%m%dT%H%M%S' if len(value) == 15 else '%Y%m%dT%H%M'
            parsed = timezone.make_aware(datetime.strptime(value, fmt), italy_tz)
        return parsed, False

    @staticmethod
    def _clean_ics_text(raw_value):
        return (
            raw_value.strip()
            .replace('\\n', ' ')
            .replace('\\,', ',')
            .replace('\\;', ';')
            .replace('\\\\', '\\')
        )

    @staticmethod
    def _parse_rrule(raw_value):
        parsed = {}
        for part in raw_value.strip().split(';'):
            if '=' not in part:
                continue
            key, value = part.split('=', 1)
            parsed[key.upper()] = value
        return parsed

    @staticmethod
    def _occurrence_key(value):
        if isinstance(value, datetime):
            return value.replace(microsecond=0)
        return value

    @classmethod
    def _parse_exdates(cls, raw_value):
        exdates = set()
        for value in raw_value.split(','):
            parsed, _ = cls._parse_ics_datetime(value)
            exdates.add(cls._occurrence_key(parsed))
        return exdates

    @classmethod
    def _detect_rooms(cls, event):
        searchable = ' '.join(
            event.get(field, '') for field in ('summary', 'location', 'description')
        ).lower()
        if 'tutto' in searchable:
            return [
                {
                    'key': key,
                    'label': label,
                }
                for key, label in cls.ROOM_TYPES
            ]

        rooms = [
            {
                'key': key,
                'label': label,
            }
            for key, label in cls.ROOM_TYPES
            if key.replace('-', ' ') in searchable
        ]
        if rooms:
            return rooms
        return [{'key': 'other', 'label': 'Altro'}]

    @classmethod
    def _expand_event_occurrences(cls, event):
        rrule = event.get('rrule')
        if not rrule:
            return [event]

        if rrule.get('FREQ') != 'WEEKLY':
            return [event]

        start = event['start']
        end = event['end']
        if not isinstance(start, datetime) or not isinstance(end, datetime):
            return [event]

        interval = int(rrule.get('INTERVAL', '1'))
        weekdays = [
            cls.RRULE_WEEKDAYS[day]
            for day in rrule.get('BYDAY', '').split(',')
            if day in cls.RRULE_WEEKDAYS
        ]
        if not weekdays:
            weekdays = [start.weekday()]

        until_raw = rrule.get('UNTIL')
        until = None
        if until_raw:
            until, _ = cls._parse_ics_datetime(until_raw)

        duration = end - start
        exdates = event.get('exdates', set())
        occurrences = []
        week_start = start.date() - timedelta(days=start.weekday())
        generated = 0
        max_generated = 370

        while generated < max_generated:
            for weekday in weekdays:
                occurrence_date = week_start + timedelta(days=weekday)
                occurrence_start = datetime.combine(
                    occurrence_date,
                    start.timetz(),
                    tzinfo=start.tzinfo,
                )

                if occurrence_start < start:
                    continue
                if until and occurrence_start > until:
                    return occurrences
                if cls._occurrence_key(occurrence_start) in exdates:
                    continue

                occurrence = event.copy()
                occurrence['start'] = occurrence_start
                occurrence['end'] = occurrence_start + duration
                occurrences.append(occurrence)
                generated += 1
                if generated >= max_generated:
                    break

            week_start += timedelta(days=7 * interval)

        return occurrences

    def _fetch_occupied_by_day(self):
        calendar_ics_url = getattr(settings, 'GOOGLE_CALENDAR_ICS_URL', self.CALENDAR_ICS_URL)
        req = Request(
            calendar_ics_url,
            headers={
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache',
                'User-Agent': 'Mozilla/5.0 (compatible; polisportiva-calendar/1.0)',
            },
        )
        with urlopen(req, timeout=8) as response:
            raw = response.read().decode('utf-8', errors='ignore')

        unfolded = []
        for line in raw.splitlines():
            # iCalendar permette "folding" delle righe: spesso inizia con spazio o tab.
            # Se non lo gestiamo, possiamo perdere parti di DTSTART/DTEND e quindi
            # non marcate correttamente i giorni come occupati.
            if unfolded and line and line[0].isspace():
                unfolded[-1] += line[1:]
            else:
                unfolded.append(line)

        events = []
        current = {}
        in_event = False
        for line in unfolded:
            if line == 'BEGIN:VEVENT':
                current = {}
                in_event = True
                continue
            if line == 'END:VEVENT' and in_event:
                if current.get('start') and current.get('end'):
                    events.append(current)
                in_event = False
                continue
            if not in_event or ':' not in line:
                continue

            key, value = line.split(':', 1)
            key = key.split(';', 1)[0]
            if key == 'DTSTART':
                current['start'], current['all_day'] = self._parse_ics_datetime(value)
            elif key == 'DTEND':
                current['end'], _ = self._parse_ics_datetime(value)
            elif key == 'SUMMARY':
                current['summary'] = self._clean_ics_text(value)
            elif key == 'LOCATION':
                current['location'] = self._clean_ics_text(value)
            elif key == 'DESCRIPTION':
                current['description'] = self._clean_ics_text(value)
            elif key == 'RRULE':
                current['rrule'] = self._parse_rrule(value)
            elif key == 'EXDATE':
                current.setdefault('exdates', set()).update(self._parse_exdates(value))

        occupied_by_day = defaultdict(list)
        expanded_events = []
        for event in events:
            expanded_events.extend(self._expand_event_occurrences(event))

        for event in expanded_events:
            start = event['start']
            end = event['end']
            all_day = event['all_day']
            rooms = self._detect_rooms(event)

            if all_day:
                current_day = start
                end_day = end - timedelta(days=1)
                while current_day <= end_day:
                    occupied_by_day[current_day].append(
                        {
                            'time': 'Tutto il giorno',
                            'rooms': rooms,
                        }
                    )
                    current_day += timedelta(days=1)
                continue

            current_day = start.date()
            end_day = end.date()
            if end.time() == datetime.min.time() and end_day > current_day:
                end_day -= timedelta(days=1)

            while current_day <= end_day:
                if current_day == start.date() and current_day == end.date():
                    time_label = f"{start.strftime('%H:%M')} - {end.strftime('%H:%M')}"
                elif current_day == start.date():
                    time_label = f"Dalle {start.strftime('%H:%M')}"
                elif current_day == end.date():
                    time_label = f"Fino alle {end.strftime('%H:%M')}"
                else:
                    time_label = 'Tutto il giorno'

                occupied_by_day[current_day].append(
                    {
                        'time': time_label,
                        'rooms': rooms,
                    }
                )
                current_day += timedelta(days=1)

        return self._merge_duplicate_slots(occupied_by_day)

    @staticmethod
    def _merge_duplicate_slots(occupied_by_day):
        optimized = defaultdict(list)
        for day, slots in occupied_by_day.items():
            slot_by_time = {}
            for slot in slots:
                time_label = slot['time']
                if time_label not in slot_by_time:
                    slot_by_time[time_label] = {
                        'time': time_label,
                        'rooms': [],
                    }
                    optimized[day].append(slot_by_time[time_label])

                existing_room_keys = {
                    room['key'] for room in slot_by_time[time_label]['rooms']
                }
                for room in slot['rooms']:
                    if room['key'] in existing_room_keys:
                        continue
                    slot_by_time[time_label]['rooms'].append(room)
                    existing_room_keys.add(room['key'])

        return optimized

    def _selected_month(self):
        raw = self.request.GET.get('month', '')
        try:
            selected = datetime.strptime(raw, '%Y-%m').date()
            return date(selected.year, selected.month, 1)
        except ValueError:
            today = timezone.localdate()
            return date(today.year, today.month, 1)

    @staticmethod
    def _shift_month(base_month, delta):
        year = base_month.year + ((base_month.month - 1 + delta) // 12)
        month = ((base_month.month - 1 + delta) % 12) + 1
        return date(year, month, 1)

    def _build_month_grid(self, month_start, occupied_by_day):
        cal = calendar.Calendar(firstweekday=0)
        weeks = []
        for week in cal.monthdatescalendar(month_start.year, month_start.month):
            week_cells = []
            for day in week:
                slots = occupied_by_day.get(day, [])
                week_cells.append(
                    {
                        'date': day,
                        'in_month': day.month == month_start.month,
                        'occupied': bool(slots),
                        'slots': slots,
                    }
                )
            weeks.append(week_cells)
        return weeks

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            occupied_by_day = self._fetch_occupied_by_day()
            calendar_error = ''
        except Exception as exc:
            logger.warning('Errore caricamento calendario ICS: %s', exc)
            occupied_by_day = defaultdict(list)
            calendar_error = 'Calendario temporaneamente non disponibile.'

        month_start = self._selected_month()
        month_end = self._shift_month(month_start, 1)  # primo giorno del mese successivo
        prev_month = self._shift_month(month_start, -1)
        next_month = self._shift_month(month_start, 1)

        # Conteggio utile per debugging sincronizzazione con Google Calendar
        occupied_days_in_month = [
            d for d in sorted(occupied_by_day.keys()) if month_start <= d < month_end
        ]

        context.update(
            {
                'calendar_error': calendar_error,
                'weekday_labels': self.WEEKDAY_LABELS,
                'month_label': f"{self.MONTH_NAMES[month_start.month - 1]} {month_start.year}",
                'month_weeks': self._build_month_grid(month_start, occupied_by_day),
                'prev_month': prev_month.strftime('%Y-%m'),
                'next_month': next_month.strftime('%Y-%m'),
                'calendar_debug': {
                    'ics_url': getattr(settings, 'GOOGLE_CALENDAR_ICS_URL', self.CALENDAR_ICS_URL),
                    'occupied_days_in_month': len(occupied_days_in_month),
                    'occupied_days': [
                        {
                            'date': d,
                            'slots': occupied_by_day[d],
                        }
                        for d in occupied_days_in_month
                    ],
                },
            }
        )
        return context

class CiclismoView(TemplateView):
    template_name = 'home/ciclismo.html'


def robots_txt(request):
    """robots.txt generato dinamicamente con link al sitemap."""
    site_url = getattr(settings, 'SITE_URL', '').rstrip('/')
    lines = [
        'User-agent: *',
        'Disallow: /admin/',
        'Disallow: /eventi/paypal/',
        'Disallow: /eventi/pagamento/',
        'Disallow: /eventi/conferma/',
        'Allow: /',
        '',
        f'Sitemap: {site_url}/sitemap.xml',
    ]
    return HttpResponse('\n'.join(lines), content_type='text/plain')


class ContattiView(FormView):
    template_name = 'home/contatti.html'
    form_class = ContattoForm
    success_url = reverse_lazy('contatti')

    def form_valid(self, form):
        d = form.cleaned_data
        send_mail(
            subject=f"[Contatto sito] {d['oggetto']}",
            message=(
                f"Nome: {d['nome']}\n"
                f"Email: {d['email']}\n\n"
                f"{d['messaggio']}"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.CONTACT_EMAIL],
            fail_silently=False,
        )
        messages.success(self.request, 'Messaggio inviato con successo! Ti risponderemo al più presto.')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Correggi gli errori nel modulo.')
        return super().form_invalid(form)
