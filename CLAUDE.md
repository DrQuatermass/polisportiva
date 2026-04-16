# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

A website for a Sammarinese sports club (polisportiva), inspired by [ciclistica2000.it](https://www.ciclistica2000.it/). Content-focused with Django admin for easy management. Simple, responsive, sports/institutional style.

## Commands

```bash
# Activate virtualenv (Windows)
source venv/Scripts/activate

# Run dev server
python manage.py runserver

# Apply migrations
python manage.py migrate

# Create migrations after model changes
python manage.py makemigrations

# Run tests
python manage.py test

# Run tests for a single app
python manage.py test home

# Create a new app
python manage.py startapp <appname>

# Open Django shell
python manage.py shell

# Create superuser
python manage.py createsuperuser
```

## Architecture

### Project layout

- `config/` — Django project package (settings, root URLs, wsgi/asgi)
- `home/` — first app (homepage, static pages); stub only so far
- `manage.py` — Django CLI entry point
- `venv/` — virtual environment

### Planned apps (not yet created)

- `news` — articles / press releases
- `events` — sports/cultural events, with registration forms and document uploads
- `teams` — squads / categories

### URL routing

Root URLconf is `config/urls.py`. Each app should have its own `urls.py`, included via `include()` in the root conf.

### Templates

Use `base.html` with `{% extends %}`. Templates live in each app's `templates/<appname>/` directory. `APP_DIRS = True` is set so Django discovers them automatically.

### Settings

Single `config/settings.py` for now. Database is SQLite (`db.sqlite3` at project root). No `.env` yet — add one with `python-decouple` or `django-environ` when secrets management is needed.

## Coding conventions

- Use class-based views (`ListView`, `DetailView`, `TemplateView`, etc.)
- Register every model in `admin.py` with `search_fields`, `list_filter`, and `ordering`
- Use slugs for URL-friendly identifiers on `News`, `Event`, `Team`
- Mobile-first HTML with semantic tags (`<header>`, `<section>`, `<footer>`)
- No inline styles; use reusable CSS classes
- Brand colors: red `#dc2626`, white `#ffffff`, light gray `#f3f4f6`
- Font: sans-serif (Inter or Open Sans)
