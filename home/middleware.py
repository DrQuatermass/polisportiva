import gzip as _gzip


class SocialCrawlerPlainHtmlMiddleware:
    """Serve plain, uncached HTML to Facebook crawlers.

    Some social scrapers are brittle when HTML is cached and compressed through
    multiple middleware/proxy layers. Keep normal browser responses unchanged.
    """

    FACEBOOK_CRAWLERS = ('facebookexternalhit', 'facebot')

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
        is_facebook = any(crawler in user_agent for crawler in self.FACEBOOK_CRAWLERS)
        if is_facebook:
            request.META['HTTP_ACCEPT_ENCODING'] = 'identity'

        response = self.get_response(request)

        if is_facebook and response.get('Content-Type', '').startswith('text/html'):
            response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
            if response.get('Content-Encoding') == 'gzip':
                response.content = _gzip.decompress(response.content)
                del response['Content-Encoding']
                del response['Content-Length']

        return response
