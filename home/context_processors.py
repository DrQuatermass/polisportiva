from django.conf import settings


def analytics(request):
    return {
        'GOOGLE_ANALYTICS_ID': getattr(settings, 'GOOGLE_ANALYTICS_ID', ''),
        'GOOGLE_SITE_VERIFICATION': getattr(settings, 'GOOGLE_SITE_VERIFICATION', ''),
    }


def site(request):
    """Espone nome, descrizione e URL canonico del sito ai template (per SEO/OG)."""
    site_url = getattr(settings, 'SITE_URL', '').rstrip('/\\')
    # URL assoluto della pagina corrente (evita duplicazione di https se build_absolute_uri in HTTPS)
    try:
        canonical_url = request.build_absolute_uri(request.path)
    except Exception:
        canonical_url = f"{site_url}{request.path}" if site_url else request.path

    return {
        'SITE_URL': site_url,
        'SITE_NAME': getattr(settings, 'SITE_NAME', 'Polisportiva Sanmarinese'),
        'SITE_DESCRIPTION': getattr(settings, 'SITE_DESCRIPTION', ''),
        'CANONICAL_URL': canonical_url,
    }
