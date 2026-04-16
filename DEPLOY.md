# Deploy — polisportivasanmarinese.it
### VPS Aruba · Ubuntu 22.04 · Apache2 + Gunicorn

---

## FASE 1 — Preparazione VPS

### 1.1 Accesso e utente

```bash
# Accedi via SSH come root
ssh root@IP_DEL_VPS

# Crea utente dedicato
adduser polisportiva
usermod -aG sudo polisportiva

# Torna a lavorare come utente normale
su - polisportiva
```

### 1.2 Aggiorna il sistema

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y software-properties-common git apache2 \
    python3-dev libpq-dev build-essential

# Django 6 richiede Python 3.12+
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.12 python3.12-venv python3.12-dev
python3.12 --version
```

---

## FASE 2 — Codice sul server

### 2.1 Carica il progetto

**Opzione A — Git (consigliata)**
```bash
cd /var/www
sudo mkdir polisportiva
sudo chown polisportiva:polisportiva polisportiva
cd polisportiva
git clone https://github.com/DrQuatermass/polisportiva.git .
```

**Opzione B — Upload diretto con scp (dal tuo PC Windows)**
```bash
# Esegui dal terminale del tuo PC
scp -r C:/polisportiva/* polisportiva@IP_DEL_VPS:/var/www/polisportiva/
```

### 2.2 Virtualenv e dipendenze

```bash
cd /var/www/polisportiva
python3.12 -m venv venv
source venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt
```

---

## FASE 3 — Settings di produzione

### 3.1 File `.env` (credenziali separate dal codice)

```bash
nano /var/www/polisportiva/.env
```

Contenuto del file `.env`:
```
SECRET_KEY=genera-una-chiave-sicura-qui
DEBUG=False
ALLOWED_HOSTS=polisportivasanmarinese.it,www.polisportivasanmarinese.it
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
GOOGLE_CALENDAR_ICS_URL=https://calendar.google.com/calendar/ical/.../private-.../basic.ics
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
CONTACT_EMAIL=polisportivasanmarinese@gmail.com
PAYPAL_MODE=sandbox
PAYPAL_CLIENT_ID=
```

Durante i test da server, se usi `curl http://127.0.0.1` o l'IP pubblico, aggiungi anche `127.0.0.1,localhost,IP_DEL_VPS` ad `ALLOWED_HOSTS`, oppure passa l'header Host del dominio:

```bash
curl -I -H "Host: polisportivasanmarinese.it" http://127.0.0.1
```

Per generare una SECRET_KEY sicura:
```bash
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 3.2 Settings di produzione

`config/settings.py` legge gia' le variabili da `.env`; non inserire credenziali o chiavi nel codice. Il blocco seguente e' un riferimento storico e non va applicato se stai usando questa versione del repository:

```python
from pathlib import Path
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='').split(',')

# Static files — in produzione Apache serve /var/www/polisportiva/staticfiles/
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'   # <-- cartella creata da collectstatic

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Email in produzione
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
```

### 3.3 WhiteNoise

WhiteNoise non e' richiesto da questa configurazione Apache. Aggiungilo solo se vuoi servire gli statici direttamente da Django:
```python
'whitenoise.middleware.WhiteNoiseMiddleware',
```

### 3.4 Raccogli i file statici

```bash
cd /var/www/polisportiva
source venv/bin/activate
python manage.py collectstatic --noinput
python manage.py migrate
python manage.py createsuperuser
```

---

## FASE 4 — Gunicorn come servizio systemd

### 4.1 Crea il socket e il servizio

Nei file systemd non copiare le righe Markdown tipo ```ini o ```: devono esserci solo direttive systemd.

```bash
sudo nano /etc/systemd/system/polisportiva-gunicorn.socket
```

```ini
[Unit]
Description=Polisportiva Gunicorn socket

[Socket]
ListenStream=/run/polisportiva-gunicorn.sock

[Install]
WantedBy=sockets.target
```

In alternativa, puoi scrivere il socket direttamente:

```bash
sudo tee /etc/systemd/system/polisportiva-gunicorn.socket >/dev/null <<'EOF'
[Unit]
Description=Polisportiva Gunicorn socket

[Socket]
ListenStream=/run/polisportiva-gunicorn.sock

[Install]
WantedBy=sockets.target
EOF
```

```bash
sudo nano /etc/systemd/system/polisportiva-gunicorn.service
```

```ini
[Unit]
Description=gunicorn daemon
Requires=polisportiva-gunicorn.socket
After=network.target

[Service]
User=polisportiva
Group=www-data
WorkingDirectory=/var/www/polisportiva
ExecStart=/var/www/polisportiva/venv/bin/gunicorn \
    --access-logfile - \
    --workers 3 \
    --bind unix:/run/polisportiva-gunicorn.sock \
    config.wsgi:application

[Install]
WantedBy=multi-user.target
```

In alternativa, puoi scrivere il servizio direttamente:

```bash
sudo tee /etc/systemd/system/polisportiva-gunicorn.service >/dev/null <<'EOF'
[Unit]
Description=gunicorn daemon
Requires=polisportiva-gunicorn.socket
After=network.target

[Service]
User=polisportiva
Group=www-data
WorkingDirectory=/var/www/polisportiva
ExecStart=/var/www/polisportiva/venv/bin/gunicorn --access-logfile - --workers 3 --bind unix:/run/polisportiva-gunicorn.sock config.wsgi:application

[Install]
WantedBy=multi-user.target
EOF
```

### 4.2 Avvia e abilita Gunicorn

```bash
sudo systemctl start polisportiva-gunicorn.socket
sudo systemctl enable polisportiva-gunicorn.socket
sudo systemctl status polisportiva-gunicorn.socket

# Verifica che il socket esista
ls /run/polisportiva-gunicorn.sock
```

Se `polisportiva-gunicorn.service` fallisce con `status=217/USER`, l'utente indicato in `User=polisportiva` non esiste. Crealo e assegna il progetto:

```bash
sudo adduser --disabled-password --gecos "" polisportiva
sudo chown -R polisportiva:www-data /var/www/polisportiva
sudo systemctl daemon-reload
sudo systemctl restart polisportiva-gunicorn.socket
sudo systemctl restart polisportiva-gunicorn.service
```

---

## FASE 5 — Configurazione Apache2

### 5.1 Abilita i moduli necessari

```bash
sudo a2enmod proxy proxy_http headers rewrite
sudo systemctl restart apache2
```

### 5.2 Virtual host HTTP (porta 80)

Nel file Apache non copiare le righe Markdown tipo ```apache o ```: devono esserci solo direttive Apache.

```bash
sudo nano /etc/apache2/sites-available/polisportiva.conf
```

```apache
<VirtualHost *:80>
    ServerName polisportivasanmarinese.it
    ServerAlias www.polisportivasanmarinese.it

    # Redirect HTTP → HTTPS (attivare dopo aver configurato SSL)
    # RewriteEngine On
    # RewriteRule ^ https://%{HTTP_HOST}%{REQUEST_URI} [R=301,L]

    # Proxy a Gunicorn
    ProxyPreserveHost On
    ProxyPass /static/ !
    ProxyPass /media/  !
    ProxyPass / unix:/run/polisportiva-gunicorn.sock|http://localhost/
    ProxyPassReverse / unix:/run/polisportiva-gunicorn.sock|http://localhost/

    # File statici serviti da Apache
    Alias /static/ /var/www/polisportiva/staticfiles/
    <Directory /var/www/polisportiva/staticfiles>
        Require all granted
        Options -Indexes
    </Directory>

    Alias /media/ /var/www/polisportiva/media/
    <Directory /var/www/polisportiva/media>
        Require all granted
        Options -Indexes
    </Directory>

    # Header di sicurezza
    Header always set X-Content-Type-Options nosniff
    Header always set X-Frame-Options DENY
    RequestHeader set X-Forwarded-Proto "http"

    ErrorLog ${APACHE_LOG_DIR}/polisportiva_error.log
    CustomLog ${APACHE_LOG_DIR}/polisportiva_access.log combined
</VirtualHost>
```

In alternativa, puoi scrivere il file direttamente senza copiare i delimitatori Markdown:

```bash
sudo tee /etc/apache2/sites-available/polisportiva.conf >/dev/null <<'EOF'
<VirtualHost *:80>
    ServerName polisportivasanmarinese.it
    ServerAlias www.polisportivasanmarinese.it

    ProxyPreserveHost On
    ProxyPass /static/ !
    ProxyPass /media/  !
    ProxyPass / unix:/run/polisportiva-gunicorn.sock|http://localhost/
    ProxyPassReverse / unix:/run/polisportiva-gunicorn.sock|http://localhost/

    Alias /static/ /var/www/polisportiva/staticfiles/
    <Directory /var/www/polisportiva/staticfiles>
        Require all granted
        Options -Indexes
    </Directory>

    Alias /media/ /var/www/polisportiva/media/
    <Directory /var/www/polisportiva/media>
        Require all granted
        Options -Indexes
    </Directory>

    Header always set X-Content-Type-Options nosniff
    Header always set X-Frame-Options DENY
    RequestHeader set X-Forwarded-Proto "http"

    ErrorLog ${APACHE_LOG_DIR}/polisportiva_error.log
    CustomLog ${APACHE_LOG_DIR}/polisportiva_access.log combined
</VirtualHost>
EOF
```

### 5.3 Attiva il sito

```bash
sudo a2ensite polisportiva.conf
sudo a2dissite 000-default.conf   # disabilita il sito default
sudo apache2ctl configtest         # verifica la sintassi
sudo systemctl reload apache2
```

---

## FASE 6 — DNS su Aruba

Nel pannello Aruba → **Domini** → `polisportivasanmarinese.it` → **Gestione DNS**:

| Tipo | Nome | Valore | TTL |
|------|------|--------|-----|
| A | @ | IP_DEL_VPS | 3600 |
| A | www | IP_DEL_VPS | 3600 |

La propagazione DNS richiede **da 10 minuti a 24 ore**.

Verifica propagazione:
```bash
# Da qualsiasi terminale
nslookup polisportivasanmarinese.it
# oppure
dig polisportivasanmarinese.it
```

---

## FASE 7 — HTTPS con Let's Encrypt (Certbot)

```bash
sudo apt install -y certbot python3-certbot-apache

# Ottieni il certificato (dominio già propagato!)
sudo certbot --apache -d polisportivasanmarinese.it -d www.polisportivasanmarinese.it

# Certbot modifica automaticamente il conf Apache e aggiunge il redirect HTTP→HTTPS
# Verifica rinnovo automatico
sudo certbot renew --dry-run
```

Dopo Certbot, nel virtualhost HTTPS `*:443` aggiungi dentro il blocco `<VirtualHost>`:

```apache
RequestHeader set X-Forwarded-Proto "https"
```

Poi verifica e ricarica:

```bash
sudo apache2ctl configtest
sudo systemctl reload apache2
sudo systemctl restart polisportiva-gunicorn.service
```

Il certificato si rinnova automaticamente ogni 90 giorni.

Verifica che il rinnovo automatico sia attivo tramite systemd timer:

```bash
sudo systemctl status certbot.timer
sudo systemctl enable --now certbot.timer
systemctl list-timers | grep certbot
```

Il dry-run deve completarsi senza errori:

```bash
sudo certbot renew --dry-run
```

Se vuoi forzare un reload di Apache dopo ogni rinnovo riuscito, aggiungi un deploy hook:

```bash
sudo mkdir -p /etc/letsencrypt/renewal-hooks/deploy
sudo tee /etc/letsencrypt/renewal-hooks/deploy/reload-apache.sh >/dev/null <<'EOF'
#!/bin/sh
systemctl reload apache2
EOF
sudo chmod +x /etc/letsencrypt/renewal-hooks/deploy/reload-apache.sh
```

---

## FASE 8 — Permessi cartelle

```bash
# La cartella media deve essere scrivibile da Gunicorn
sudo chown -R polisportiva:www-data /var/www/polisportiva/media
sudo chmod -R 775 /var/www/polisportiva/media

# Staticfiles in sola lettura per Apache
sudo chown -R polisportiva:www-data /var/www/polisportiva/staticfiles
sudo chmod -R 755 /var/www/polisportiva/staticfiles
```

---

## FASE 9 — Firewall

```bash
sudo ufw allow 'Apache Full'   # porta 80 e 443
sudo ufw allow OpenSSH         # mantieni SSH aperto!
sudo ufw enable
sudo ufw status
```

---

## Comandi utili post-deploy

```bash
# Riavvia Gunicorn dopo modifiche al codice
sudo systemctl restart polisportiva-gunicorn

# Ricarica Apache dopo modifiche al conf
sudo systemctl reload apache2

# Log errori in tempo reale
sudo tail -f /var/log/apache2/polisportiva_error.log
sudo journalctl -u polisportiva-gunicorn -f

# Aggiorna il codice (se usi Git)
cd /var/www/polisportiva
git pull
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart polisportiva-gunicorn
```

---

## Checklist finale

- [ ] VPS raggiungibile via SSH
- [ ] Progetto caricato in `/var/www/polisportiva/`
- [ ] `.env` creato con SECRET_KEY, DEBUG=False, ALLOWED_HOSTS
- [ ] `collectstatic` e `migrate` eseguiti
- [ ] polisportiva-gunicorn.socket attivo (`systemctl status polisportiva-gunicorn.socket`)
- [ ] Apache risponde su `http://IP_DEL_VPS`
- [ ] DNS Aruba puntano all'IP del VPS
- [ ] Certbot installato, HTTPS attivo
- [ ] Sito raggiungibile su `https://polisportivasanmarinese.it`
- [ ] Admin funzionante su `/admin/`
- [ ] Upload media funzionante
