# Ottimizzazioni SEO & PageSpeed — Polisportiva Sanmarinese

Riepilogo degli interventi eseguiti e istruzioni per finalizzare il deploy su **Gunicorn + Apache2**.

## 1. Cosa è cambiato nel codice

### SEO on-page
- `templates/base.html` completamente rifatto con:
  - `<title>`, `<meta name="description">`, `<link rel="canonical">`, `<meta name="robots">` con default e override per pagina tramite block Django.
  - Open Graph (`og:type`, `og:title`, `og:description`, `og:image`, `og:url`, `og:site_name`, `og:locale`) e Twitter Card `summary_large_image`.
  - JSON-LD `SportsOrganization` sempre presente (logo, indirizzo, P.IVA, CF, email).
  - Favicon + `theme-color`, skip-link accessibilità, `<main>`/`<address>`/`<time>` semantici, `aria-*` su navbar.
- **Home** (`home/index.html`): JSON-LD `WebSite`, meta description dedicata, preload dell'hero come LCP.
- **Detail News**: JSON-LD `NewsArticle` + `BreadcrumbList`, OG dinamici con immagine della notizia.
- **Detail Eventi**: JSON-LD `Event` (incluso `Offer` quando le iscrizioni sono aperte) + `BreadcrumbList`.
- **Detail Documenti**: `BreadcrumbList` e meta description dedicata.
- Meta description dedicata anche su: `chi_siamo`, `ciclismo`, `contatti`, `calendario` (con `noarchive`), `news/list`, `events/list`, `sponsors/list`, `documents/list`.
- **`robots.txt`** generato dinamicamente (`home/views.py::robots_txt`), blocca admin e URL di pagamento, punta al sitemap.
- Sitemap già presente in `config/sitemaps.py` — ora referenziata dal `robots.txt`.

### Modelli
- `News`, `Event`, `Document` ora hanno il campo **`meta_description`** (max 160) e, dove sensato, **`og_image`** (1200×630). Se vuoti, vengono generati al volo dal contenuto.
- Admin aggiornati con fieldset "SEO & Social" collassabile.
- Migration create: `news/0002_news_seo_fields.py`, `events/0005_event_seo_fields.py`, `documents/0004_document_meta_description.py`.

### Performance (PageSpeed / Core Web Vitals)
- **WhiteNoise** aggiunto (`whitenoise[brotli]`) in MIDDLEWARE subito dopo `SecurityMiddleware`.
- Storage `CompressedManifestStaticFilesStorage`: hash automatici sui static + `.gz` + `.br` precompressi + `Cache-Control: max-age=1 year, immutable`.
- `GZipMiddleware` come fallback per risposte HTML.
- Cache per-site (`UpdateCacheMiddleware` + `FetchFromCacheMiddleware`) con TTL configurabile via `CACHE_MIDDLEWARE_SECONDS` (default 300 s, LocMemCache).
- `<link rel="preconnect">` verso `cdn.jsdelivr.net` e (se attivo GA) `googletagmanager.com`.
- Bootstrap JS caricato con `defer` (prima era bloccante).
- CSS Bootstrap/icons dal CDN (cache condivisa), CSS custom servito con hash immutable.
- Immagini: `width`/`height` espliciti su tutte le `<img>` (elimina Cumulative Layout Shift), `loading="lazy"` su quelle below-the-fold, `fetchpriority="high"` + `loading="eager"` sulle LCP (hero, immagine article/event).
- Sostituite varianti `.jpg/.png` pesanti con `.webp` dove disponibili: logo (140→3 KB), murale (1 MB→82 KB), velodromo (88→61 KB), hero (3.3 MB → 74 KB via CSS `url('../images/hero.webp')`).
- Preload dell'hero come risorsa LCP sulla home.
- Google Analytics: `anonymize_ip: true` e caricato async.

### Security headers (anche Lighthouse "Best Practices")
- `SECURE_CONTENT_TYPE_NOSNIFF = True`
- `SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'`
- `X_FRAME_OPTIONS = 'SAMEORIGIN'`
- HSTS / HTTPS redirect / cookie secure restano configurabili via `.env` (già presenti prima).

### Dipendenze nuove (`requirements.txt`)
- `whitenoise[brotli]==6.11.0` — unica aggiunta.

## 2. Cosa fare al prossimo deploy

```bash
# 1. Attiva il venv e aggiorna dipendenze
source venv/Scripts/activate          # Windows / dev
# oppure: source venv/bin/activate    # Linux / produzione
pip install -r requirements.txt

# 2. Applica le migration SEO
python manage.py migrate

# 3. Raccogli gli static con hash + precompressione gzip/brotli
python manage.py collectstatic --noinput

# 4. Riavvia Gunicorn
sudo systemctl restart gunicorn       # o come configurato nel server
```

### Configurazione Apache2 consigliata

Non è più strettamente necessario fare proxy ai file static: WhiteNoise li serve con brotli/gzip e header immutable. Ma, per togliere ancora carico a Django, si può continuare ad usare Apache:

```apache
# /etc/apache2/sites-available/polisportivasanmarinese.conf
<VirtualHost *:443>
    ServerName polisportivasanmarinese.it

    # --- Compressione ---
    AddOutputFilterByType DEFLATE text/html text/plain text/css application/javascript application/json image/svg+xml
    # meglio se hai mod_brotli:
    # AddOutputFilterByType BROTLI_COMPRESS text/html text/plain text/css application/javascript application/json image/svg+xml

    # --- Static e media serviti da Apache (più veloce di WhiteNoise) ---
    Alias /static/ /path/al/progetto/staticfiles/
    <Directory /path/al/progetto/staticfiles/>
        Require all granted
        Header set Cache-Control "public, max-age=31536000, immutable"
    </Directory>

    Alias /media/ /path/al/progetto/media/
    <Directory /path/al/progetto/media/>
        Require all granted
        Header set Cache-Control "public, max-age=2592000"
    </Directory>

    # --- Proxy a Gunicorn ---
    ProxyPass /static/ !
    ProxyPass /media/ !
    ProxyPass / http://127.0.0.1:8000/
    ProxyPassReverse / http://127.0.0.1:8000/

    RequestHeader set X-Forwarded-Proto "https"

    # HSTS (dopo aver validato il certificato)
    Header always set Strict-Transport-Security "max-age=31536000; includeSubDomains"
</VirtualHost>
```

Variabili in `.env` consigliate in produzione:

```
DEBUG=False
SECRET_KEY=<generare con: python -c "import secrets; print(secrets.token_urlsafe(50))">
ALLOWED_HOSTS=polisportivasanmarinese.it,www.polisportivasanmarinese.it
SITE_URL=https://polisportivasanmarinese.it
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
CACHE_MIDDLEWARE_SECONDS=300
```

## 3. Azioni manuali consigliate (non automatizzabili)

1. **Compilare `meta_description` nell'admin** per le prime 5-10 notizie/eventi più importanti (max 160 caratteri). Per tutto il resto funziona il fallback automatico.
2. **Google Search Console**: aggiungere il dominio, verificare con `GOOGLE_SITE_VERIFICATION`, inviare `https://polisportivasanmarinese.it/sitemap.xml`.
3. **Rich Results Test**: incollare alcune URL su <https://search.google.com/test/rich-results> per validare JSON-LD.
4. **Ottimizzare l'hero.jpg** (3.3 MB in `media/events/` e `static/images/`): già sostituito da `hero.webp` (74 KB), ma conviene cancellare i `.jpg` giganti dopo conferma che non sono più referenziati (`git grep hero.jpg`).
5. **tartaruga.svg** pesa 1.1 MB: probabilmente contiene un'immagine raster embeddata in base64. Ri-esportare come SVG pulito o sostituire con PNG ottimizzato.
6. **PageSpeed Insights**: <https://pagespeed.web.dev/> dopo il deploy, target ≥ 90 mobile.

## 4. Test rapido post-deploy

```bash
curl -I https://polisportivasanmarinese.it/static/css/style.css
# Atteso: Cache-Control: max-age=31536000, immutable
#         Content-Encoding: br  (o gzip)

curl -s https://polisportivasanmarinese.it/robots.txt
# Atteso: User-agent: * / Sitemap: ...

curl -s https://polisportivasanmarinese.it/ | grep -E '(og:|twitter:|canonical|description)'
```
