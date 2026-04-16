# Piano di implementazione — Sito Polisportiva Sanmarinese di Carpi
*Basato sulle email di Roberto Rossi (3–4 aprile 2026) — Aggiornato il 13/04/2026*

---

## Stato di avanzamento

| # | Richiesta di Roberto | Stato |
|---|----------------------|-------|
| 1 | Aggiornamento URL calendario Google | ✅ Già ok (confermato) |
| 2 | App `documents` per PDF scaricabili | ✅ Implementato |
| 3 | Sezione Affiliazioni (FCI, UISP, ARCI) in Chi siamo | ✅ Implementato |
| 4 | Banner 5x1000 (CF: 81003900362) in homepage e footer | ✅ Implementato |
| 5 | Sezione Safeguarding in Chi siamo + documenti | ✅ Implementato |
| 6 | Sezione Codice Etico & Carta Etica in Chi siamo + documenti | ✅ Implementato |
| 7 | Caricamento loghi sponsor (buona parte già caricata) | ✅ Da completare via Admin |
| 8 | Regolamento ciclismo scaricabile nella pagina squadra | ✅ Implementato |
| 9 | Volantino promozionale A4 | 📋 Da caricare via Admin |

---

## Comandi da eseguire sulla tua macchina

Dopo aver applicato le modifiche, esegui questi comandi nella cartella del progetto:

```bash
source venv/Scripts/activate      # Windows
python manage.py migrate           # applica le migrazioni (documents + teams)
python manage.py runserver         # avvia il server
```

---

## Cosa è stato creato / modificato

### Nuova app: `documents/`
Gestisce tutti i documenti scaricabili dal sito. Accessibile da Admin → Documenti.

**Categorie disponibili:**
- `regolamento` — Regolamenti squadre
- `etico` — Codice Etico & Carta Etica dello Sport
- `safeguarding` — Documenti Safeguarding
- `privacy` — Privacy & GDPR
- `promo` — Materiale promozionale

**URL pubblica:** `/documenti/`

### File modificati
| File | Modifica |
|------|----------|
| `config/settings.py` | Aggiunta `documents` a INSTALLED_APPS |
| `config/urls.py` | Aggiunto path `/documenti/` |
| `templates/base.html` | Aggiunta voce "Documenti" in navbar e footer; banner 5x1000 nel footer; P.IVA nel copyright |
| `home/templates/home/index.html` | Aggiunto banner 5x1000 prominente |
| `home/templates/home/chi_siamo.html` | Aggiunte sezioni: Affiliazioni, Codice Etico, Safeguarding |
| `teams/models.py` | Aggiunto campo `regulation` (FileField PDF) |
| `teams/admin.py` | Mostra colonna "Regolamento" con indicatore sì/no |
| `teams/templates/teams/detail.html` | Mostra box download regolamento se presente |

---

## Operazioni da fare via Django Admin

Una volta avviato il server, accedi a `/admin/` e carica:

### Documenti (`/admin/documents/document/`)
| Titolo | Categoria | File da caricare |
|--------|-----------|-----------------|
| Regolamento PSM 2026 | Regolamenti | `REGOLAMENTO PSM 2026.pdf` |
| Codice Etico | Codice Etico & Carta Etica | `CODICE ETICO CF 7-8-2019.pdf` |
| Carta Etica dello Sport | Codice Etico & Carta Etica | `carta-etica-dello-sport-testo.pdf` |
| Numeri utili per chiedere aiuto | Safeguarding | `Numeri utili per chiedere aiuto.pdf` |
| Modulo segnalazione | Safeguarding | `Modulo segnalazione.pdf` |
| Nomina Responsabile Safeguarding | Safeguarding | `Nomina Responsabile Safeguarding.pdf` |
| Modello Organizzativo (art. 16 D.lgs 39/2021) | Safeguarding | `MODELLO ORGANIZZATIVO EX ART. 16.pdf` |
| Codice di Condotta (art. 16 D.lgs 39/2021) | Safeguarding | `CODICE DI CONDOTTA EX ART. 16.pdf` |
| GDPR — Informativa Privacy | Privacy & GDPR | `GDPR 2016_679 Privacy.pdf` |
| Volantino promozionale | Materiale promozionale | (scaricare da Google Drive) |

### Squadra ciclismo (`/admin/teams/team/`)
Aprire la squadra ciclismo e caricare `REGOLAMENTO PSM 2026.pdf` nel campo **Regolamento (PDF)**.

---

## Note aperte

- **`POL_SANMARINESE.svg`** (allegato nelle email): è il logo del club? Se sì, può sostituire `static/images/logo.jpg` nella navbar — sarebbe un aggiornamento di qualità.
- **Responsabile Safeguarding**: il nome e contatto del responsabile può essere aggiunto a mano nel template `chi_siamo.html` nella sezione Safeguarding.

