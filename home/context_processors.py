from django.conf import settings


def analytics(request):
    return {
        'GOOGLE_ANALYTICS_ID': getattr(settings, 'GOOGLE_ANALYTICS_ID', ''),
        'GOOGLE_SITE_VERIFICATION': getattr(settings, 'GOOGLE_SITE_VERIFICATION', ''),
    }
