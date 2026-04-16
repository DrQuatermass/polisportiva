from django.db import migrations
from django.utils.text import slugify


DOCUMENTS = [

    # ── REGOLAMENTI ──────────────────────────────────────────────────────────
    {
        'title': 'Regolamento Squadra Ciclismo PSM 2026',
        'category': 'regolamento',
        'order': 1,
        'description': 'Regolamento interno della squadra di ciclismo della Polisportiva Sanmarinese per la stagione 2026.',
        'content': '''<h2>Regolamento Squadra Ciclismo PSM 2026</h2>

<p><em>Il testo completo di questo documento è disponibile nel PDF allegato, scaricabile tramite il pulsante qui sotto.</em></p>

<h3>Struttura del documento</h3>
<ul>
  <li>Norme generali di comportamento</li>
  <li>Impegni degli atleti tesserati</li>
  <li>Calendario e convocazioni</li>
  <li>Utilizzo materiali e mezzi</li>
  <li>Sanzioni disciplinari</li>
</ul>

<p>Per qualsiasi chiarimento contattare la segreteria della Polisportiva Sanmarinese di Carpi.</p>''',
    },

    # ── CODICE ETICO & CARTA ETICA ───────────────────────────────────────────
    {
        'title': 'Codice Etico della Polisportiva Sanmarinese',
        'category': 'etico',
        'order': 1,
        'description': 'Il Codice Etico definisce i valori e i principi di condotta a cui si ispirano gli organi sociali, i tecnici, i collaboratori e gli atleti.',
        'content': '''<h2>Codice Etico della Polisportiva Sanmarinese di Carpi</h2>
<p><em>Approvato il 7 agosto 2019</em></p>

<h3>Art. 1 — Finalità e ambito di applicazione</h3>
<p>Il presente Codice Etico (di seguito "Codice") ha lo scopo di promuovere i valori fondanti dell'attività sportiva: lealtà, correttezza, rispetto, inclusione e tutela della salute. Si applica a tutti i soggetti che a qualsiasi titolo operano all'interno della Polisportiva Sanmarinese di Carpi (di seguito "Associazione"): dirigenti, tecnici, atleti, genitori, collaboratori e volontari.</p>

<h3>Art. 2 — Principi generali</h3>
<p>Tutti i soggetti destinatari del presente Codice si impegnano a:</p>
<ul>
  <li>Rispettare le regole dello sport praticato e lo spirito del fair play;</li>
  <li>Trattare con rispetto e dignità tutti i soggetti con cui entrano in contatto nell'ambito dell'attività associativa;</li>
  <li>Non discriminare nessuno per motivi di sesso, età, origine etnica, condizioni fisiche, orientamento sessuale, religione o convinzioni personali;</li>
  <li>Astenersi da qualsiasi comportamento violento, intimidatorio o lesivo dell'altrui dignità, sia fisicamente che verbalmente o attraverso strumenti digitali;</li>
  <li>Preservare l'immagine e la reputazione dell'Associazione.</li>
</ul>

<h3>Art. 3 — Impegni dei dirigenti e dei tecnici</h3>
<p>I dirigenti e i tecnici dell'Associazione si impegnano a:</p>
<ul>
  <li>Svolgere la propria attività con competenza, trasparenza e spirito di servizio;</li>
  <li>Anteporre gli interessi degli atleti, in particolare dei minori, a qualsiasi altra considerazione;</li>
  <li>Non sfruttare la propria posizione per ottenere benefici personali;</li>
  <li>Garantire pari opportunità di accesso all'attività sportiva;</li>
  <li>Promuovere un ambiente sicuro, inclusivo e stimolante per tutti gli atleti.</li>
</ul>

<h3>Art. 4 — Impegni degli atleti</h3>
<p>Gli atleti si impegnano a:</p>
<ul>
  <li>Rispettare i compagni di squadra, gli avversari, i tecnici, i giudici e il pubblico;</li>
  <li>Astenersi dall'uso di sostanze dopanti o di qualsiasi altra pratica che alteri artificialmente le prestazioni;</li>
  <li>Tenere un comportamento corretto in gara, in allenamento e nei contesti sociali legati all'Associazione;</li>
  <li>Comunicare tempestivamente ai tecnici eventuali problemi fisici o situazioni di disagio.</li>
</ul>

<h3>Art. 5 — Tutela dei minori</h3>
<p>L'Associazione riconosce la centralità della tutela dei minori in ogni aspetto della propria attività. Ogni soggetto che interagisce con atleti minorenni è tenuto a:</p>
<ul>
  <li>Non stabilire contatti diretti con minori al di fuori dei contesti associativi se non previa comunicazione ai genitori;</li>
  <li>Segnalare immediatamente al Responsabile Safeguarding qualsiasi situazione di rischio o comportamento inappropriato;</li>
  <li>Non fotografare o riprendere minori senza l'esplicito consenso scritto dei genitori.</li>
</ul>

<h3>Art. 6 — Violazioni e sanzioni</h3>
<p>Le violazioni del presente Codice saranno esaminate dal Consiglio Direttivo, che adotterà i provvedimenti disciplinari proporzionati alla gravità del fatto, fino all'esclusione dall'Associazione. Nei casi più gravi, verrà data comunicazione alle autorità sportive e, se necessario, alle autorità giudiziarie competenti.</p>

<h3>Art. 7 — Segnalazioni</h3>
<p>Chiunque venga a conoscenza di comportamenti contrari al presente Codice è incoraggiato a segnalarli al Responsabile Safeguarding o alla Presidenza dell'Associazione. Le segnalazioni saranno trattate con la massima riservatezza.</p>''',
    },
    {
        'title': 'Carta Etica dello Sport — Regione Emilia-Romagna',
        'category': 'etico',
        'order': 2,
        'description': 'La Polisportiva Sanmarinese ha aderito alla Carta Etica dello Sport della Regione Emilia-Romagna (n. 500 dell\'elenco).',
        'content': '''<h2>Carta Etica dello Sport</h2>
<p><em>Promossa dalla Regione Emilia-Romagna</em></p>

<p>La Polisportiva Sanmarinese di Carpi ha aderito alla <strong>Carta Etica dello Sport</strong> della Regione Emilia-Romagna, impegnandosi formalmente a promuovere i valori di lealtà, rispetto e correttezza in ogni ambito della propria attività sportiva.</p>

<p>Siamo inseriti al <strong>numero 500</strong> dell'elenco ufficiale delle società aderenti — la <strong>10ª società di Carpi</strong> a sottoscrivere questo impegno.</p>

<h3>I principi della Carta</h3>
<p>Le società aderenti si impegnano a rispettare e promuovere i seguenti principi fondamentali:</p>

<ul>
  <li><strong>Lealtà sportiva</strong> — rispettare le regole del gioco e lo spirito del fair play in ogni competizione e allenamento;</li>
  <li><strong>Rispetto delle persone</strong> — trattare con rispetto atleti, avversari, arbitri, tecnici e spettatori, indipendentemente da età, sesso, etnia, abilità o orientamento;</li>
  <li><strong>Tutela della salute</strong> — garantire condizioni di sicurezza fisica e psicologica per tutti i praticanti, con particolare attenzione ai minori;</li>
  <li><strong>Contrasto al doping</strong> — promuovere una cultura sportiva basata sul talento, l'impegno e i valori etici, rifiutando qualsiasi forma di doping;</li>
  <li><strong>Inclusione e pari opportunità</strong> — garantire l'accesso allo sport a tutti, rimuovendo qualsiasi barriera economica, culturale o sociale;</li>
  <li><strong>Contrasto alle discriminazioni</strong> — adottare misure concrete per prevenire e contrastare ogni forma di razzismo, sessismo, omofobia e discriminazione;</li>
  <li><strong>Trasparenza e corretta gestione</strong> — gestire le risorse dell'associazione in modo trasparente, nel rispetto delle norme e degli interessi degli associati;</li>
  <li><strong>Sostenibilità ambientale</strong> — promuovere comportamenti responsabili verso l'ambiente nell'organizzazione delle attività sportive.</li>
</ul>

<h3>Il nostro impegno</h3>
<p>L'adesione alla Carta non è solo un atto formale: rappresenta la volontà concreta di costruire una cultura sportiva positiva, dove ogni persona si senta valorizzata e al sicuro. Per consultare l'elenco completo delle società aderenti, visita il sito della <a href="https://www.regione.emilia-romagna.it/sport/carta-etica-dello-sport" target="_blank">Regione Emilia-Romagna</a>.</p>''',
    },

    # ── SAFEGUARDING ─────────────────────────────────────────────────────────
    {
        'title': 'Modello Organizzativo — Art. 16 D.lgs 39/2021',
        'category': 'safeguarding',
        'order': 1,
        'description': 'Modello organizzativo adottato ai sensi dell\'art. 16 comma 1 del D.lgs 39/2021 per la tutela dei minori e la prevenzione delle molestie.',
        'content': '''<h2>Modello Organizzativo</h2>
<p><em>Ai sensi dell'art. 16 comma 1 del D.lgs 28 febbraio 2021 n. 39</em></p>

<h3>1. Premessa</h3>
<p>Il Decreto Legislativo 28 febbraio 2021, n. 39 (Riforma dello Sport) ha introdotto specifici obblighi a carico delle associazioni e società sportive dilettantistiche in materia di tutela delle persone, con particolare riferimento ai minori. In adempimento agli obblighi di cui all'art. 16, la Polisportiva Sanmarinese di Carpi ha adottato il presente Modello Organizzativo.</p>

<h3>2. Ambito di applicazione</h3>
<p>Il presente Modello si applica a tutti coloro che a qualsiasi titolo svolgono attività presso la Polisportiva Sanmarinese: dirigenti, tecnici, istruttori, collaboratori, volontari e atleti maggiorenni.</p>

<h3>3. Responsabile Safeguarding</h3>
<p>L'Associazione ha nominato un <strong>Responsabile Safeguarding</strong> (di seguito RS), figura incaricata di:</p>
<ul>
  <li>Ricevere e gestire le segnalazioni di comportamenti inappropriati o situazioni di rischio;</li>
  <li>Fornire supporto e orientamento a chiunque abbia subito o sia testimone di episodi lesivi;</li>
  <li>Coordinare le azioni di prevenzione e formazione in materia di safeguarding;</li>
  <li>Mantenere i contatti con gli organismi sportivi e, se necessario, con le autorità competenti.</li>
</ul>

<h3>4. Misure preventive</h3>
<p>Per prevenire abusi, molestie e comportamenti scorretti, l'Associazione adotta le seguenti misure:</p>
<ul>
  <li>Verifica del casellario giudiziale per tutti i soggetti che operano a contatto con minori;</li>
  <li>Svolgimento degli allenamenti in ambienti visibili e accessibili;</li>
  <li>Divieto di contatti privati tra tecnici/collaboratori e atleti minorenni tramite canali di comunicazione personali;</li>
  <li>Formazione periodica del personale tecnico e dirigenziale in materia di salvaguardia;</li>
  <li>Adozione del Codice di Condotta vincolante per tutti i soggetti destinatari.</li>
</ul>

<h3>5. Procedura di segnalazione</h3>
<p>Chiunque venga a conoscenza di comportamenti inappropriati o sospetti abusi è tenuto a:</p>
<ol>
  <li>Segnalare immediatamente la situazione al Responsabile Safeguarding;</li>
  <li>Compilare il modulo di segnalazione disponibile presso la segreteria e su questo sito;</li>
  <li>In caso di emergenza o pericolo immediato, contattare le autorità competenti (Carabinieri 112, Polizia 113, Pronto Soccorso 118).</li>
</ol>

<h3>6. Riservatezza</h3>
<p>Tutte le segnalazioni saranno trattate con la massima riservatezza. Il segnalante in buona fede non subirà alcuna conseguenza negativa.</p>''',
    },
    {
        'title': 'Codice di Condotta — Art. 16 D.lgs 39/2021',
        'category': 'safeguarding',
        'order': 2,
        'description': 'Il Codice di Condotta definisce i comportamenti attesi e vietati per tutti i soggetti che operano in ambito associativo.',
        'content': '''<h2>Codice di Condotta</h2>
<p><em>Ai sensi dell'art. 16 comma 1 del D.lgs 28 febbraio 2021 n. 39</em></p>

<h3>Comportamenti richiesti a tutti i soggetti</h3>
<p>Tutti coloro che operano nell'ambito della Polisportiva Sanmarinese di Carpi — dirigenti, tecnici, collaboratori, atleti e genitori — sono tenuti a:</p>
<ul>
  <li>Trattare tutti gli atleti con rispetto, imparzialità e dignità;</li>
  <li>Promuovere un ambiente inclusivo, sicuro e positivo per la pratica sportiva;</li>
  <li>Segnalare al Responsabile Safeguarding qualsiasi situazione di rischio o comportamento inappropriato di cui vengano a conoscenza;</li>
  <li>Rispettare la privacy degli atleti, in particolare dei minori, evitando la diffusione non autorizzata di immagini o dati personali;</li>
  <li>Mantenere confini professionali adeguati in ogni interazione con gli atleti.</li>
</ul>

<h3>Comportamenti espressamente vietati</h3>
<p>È assolutamente vietato:</p>
<ul>
  <li>Qualsiasi forma di abuso fisico, psicologico, sessuale o di negligenza nei confronti degli atleti;</li>
  <li>Utilizzare un linguaggio offensivo, umiliante o sessista;</li>
  <li>Stabilire relazioni di natura personale o romantica con atleti minorenni;</li>
  <li>Contattare privatamente atleti minorenni tramite social media, app di messaggistica o altri canali digitali al di fuori dei contesti associativi ufficiali;</li>
  <li>Somministrare farmaci o integratori agli atleti senza l'autorizzazione esplicita dei genitori (per i minori) o dell'atleta stesso (per i maggiorenni);</li>
  <li>Effettuare sedute di allenamento individuali con atleti minorenni in luoghi isolati o non visibili;</li>
  <li>Fotografare o riprendere atleti minorenni senza il consenso scritto dei genitori.</li>
</ul>

<h3>Norme specifiche per i tecnici</h3>
<ul>
  <li>I contatti fisici (es. correzione della postura) devono essere limitati al necessario, avvenire in luoghi visibili e mai essere di natura intima;</li>
  <li>Eventuali riunioni individuali con atleti minorenni devono svolgersi in luoghi aperti e visibili da terzi;</li>
  <li>I tecnici devono comunicare ai genitori qualsiasi cambiamento significativo nel comportamento dell'atleta.</li>
</ul>

<h3>Violazioni e conseguenze</h3>
<p>Le violazioni del presente Codice sono sottoposte all'esame del Consiglio Direttivo, che può adottare misure disciplinari fino all'esclusione dall'Associazione, ferma restando la facoltà di procedere a segnalazione alle autorità competenti.</p>''',
    },
    {
        'title': 'Nomina Responsabile Safeguarding',
        'category': 'safeguarding',
        'order': 3,
        'description': 'Atto di nomina del Responsabile Safeguarding della Polisportiva Sanmarinese di Carpi.',
        'content': '''<h2>Nomina del Responsabile Safeguarding</h2>

<p>Il Consiglio Direttivo della <strong>Polisportiva Sanmarinese di Carpi</strong>, in ottemperanza all'obbligo previsto dall'art. 16 del D.lgs 28 febbraio 2021 n. 39 (Riforma dello Sport),</p>

<p><strong>NOMINA</strong></p>

<p>quale <strong>Responsabile Safeguarding</strong> dell'Associazione la persona indicata nel documento PDF allegato, a cui è affidato il compito di:</p>
<ul>
  <li>Ricevere e gestire le segnalazioni relative a comportamenti inappropriati o situazioni di rischio per gli atleti;</li>
  <li>Promuovere la cultura della tutela e della prevenzione all'interno dell'Associazione;</li>
  <li>Coordinare le misure organizzative di safeguarding;</li>
  <li>Essere punto di riferimento per atleti, genitori, tecnici e collaboratori in materia di tutela delle persone.</li>
</ul>

<p>Per contattare il Responsabile Safeguarding, scrivere a: <strong>info@polisportivasanmarinese.it</strong> (oggetto: "Safeguarding").</p>

<p><em>Il documento ufficiale di nomina con firma del Presidente è disponibile nel PDF allegato.</em></p>''',
    },
    {
        'title': 'Modulo di Segnalazione Safeguarding',
        'category': 'safeguarding',
        'order': 4,
        'description': 'Modulo per segnalare comportamenti inappropriati o situazioni di rischio al Responsabile Safeguarding.',
        'content': '''<h2>Modulo di Segnalazione</h2>

<p>Questo modulo è destinato a chiunque voglia segnalare al Responsabile Safeguarding un comportamento inappropriato, una situazione di rischio o un episodio che potrebbe riguardare il benessere di un atleta.</p>

<div class="alert alert-light border mb-4">
  <strong>Emergenze:</strong> In caso di pericolo immediato, non compilare questo modulo — chiama il 112 (Carabinieri) o il 113 (Polizia) immediatamente.
</div>

<h3>Come presentare una segnalazione</h3>
<p>Puoi segnalare una situazione:</p>
<ul>
  <li><strong>Via email:</strong> invia una mail a <strong>info@polisportivasanmarinese.it</strong> con oggetto "Segnalazione Safeguarding";</li>
  <li><strong>Modulo cartaceo:</strong> scarica e compila il modulo PDF allegato, consegnalo al Responsabile Safeguarding o alla segreteria in busta chiusa;</li>
  <li><strong>Di persona:</strong> parla direttamente con il Responsabile Safeguarding in un luogo riservato.</li>
</ul>

<h3>Cosa include una segnalazione</h3>
<p>Una segnalazione utile indica:</p>
<ul>
  <li>La descrizione del fatto o del comportamento osservato (dove, quando, chi era presente);</li>
  <li>Se si tratta di un episodio singolo o ricorrente;</li>
  <li>Le persone eventualmente coinvolte (atleta, tecnico, dirigente, genitore...);</li>
  <li>Eventuali testimoni;</li>
  <li>I tuoi dati di contatto (la segnalazione può essere anche anonima, ma i tuoi dati ci aiutano a fare un follow-up).</li>
</ul>

<h3>Riservatezza</h3>
<p>Tutte le segnalazioni sono gestite con la massima riservatezza. Chi segnala in buona fede non subirà alcuna conseguenza negativa. I dati personali saranno trattati nel rispetto del GDPR.</p>''',
    },
    {
        'title': 'Numeri Utili per Chiedere Aiuto',
        'category': 'safeguarding',
        'order': 5,
        'description': 'Riferimenti telefonici e risorse a cui rivolgersi in caso di bisogno o emergenza.',
        'content': '''<h2>Numeri Utili per Chiedere Aiuto</h2>

<p>Se sei in una situazione di disagio, hai subito un abuso o hai bisogno di parlare con qualcuno, questi sono i riferimenti a cui puoi rivolgerti:</p>

<h3>Emergenze</h3>
<ul>
  <li><strong>112</strong> — Numero Unico di Emergenza (Carabinieri / Polizia)</li>
  <li><strong>113</strong> — Polizia di Stato</li>
  <li><strong>118</strong> — Pronto Soccorso / Emergenza Medica</li>
  <li><strong>115</strong> — Vigili del Fuoco</li>
</ul>

<h3>Tutela dei minori</h3>
<ul>
  <li><strong>19696</strong> — Telefono Azzurro (ascolto e supporto per minori e genitori, gratuito, attivo 24h)</li>
  <li><strong>114</strong> — Emergenza Infanzia (segnalazione di situazioni di rischio per minori)</li>
</ul>

<h3>Supporto psicologico e violenza</h3>
<ul>
  <li><strong>1522</strong> — Antiviolenza e Stalking (gratuito, attivo 24h, anche via chat su 1522.eu)</li>
  <li><strong>800 274 274</strong> — Telefono Amico (ascolto e supporto psicologico)</li>
</ul>

<h3>Riferimento interno all'Associazione</h3>
<ul>
  <li><strong>Responsabile Safeguarding PSM</strong> — contattabile via email a <strong>info@polisportivasanmarinese.it</strong> (oggetto: "Safeguarding")</li>
  <li><strong>Federazione Ciclistica Italiana (FCI)</strong> — Ufficio Safeguarding: <a href="https://www.federciclismo.it" target="_blank">federciclismo.it</a></li>
  <li><strong>UISP</strong> — <a href="https://www.uisp.it" target="_blank">uisp.it</a></li>
</ul>

<h3>Risorse online</h3>
<ul>
  <li><a href="https://www.telefono-azzurro.it" target="_blank">www.telefono-azzurro.it</a></li>
  <li><a href="https://www.1522.eu" target="_blank">www.1522.eu</a> — chat antiviolenza</li>
  <li><a href="https://www.sportesalute.eu/safeguarding" target="_blank">Sport e Salute — Safeguarding</a></li>
</ul>''',
    },

    # ── PRIVACY & GDPR ───────────────────────────────────────────────────────
    {
        'title': 'Informativa Privacy — GDPR 2016/679',
        'category': 'privacy',
        'order': 1,
        'description': 'Informativa sul trattamento dei dati personali ai sensi del Regolamento UE 2016/679 (GDPR).',
        'content': '''<h2>Informativa sul Trattamento dei Dati Personali</h2>
<p><em>Ai sensi degli artt. 13 e 14 del Regolamento UE 2016/679 (GDPR)</em></p>

<h3>1. Titolare del trattamento</h3>
<p>Il Titolare del trattamento è la <strong>Polisportiva Sanmarinese di Carpi</strong>, con sede in Carpi (MO).<br>
Codice Fiscale: 81003900362 — P.IVA: 02810810362<br>
Email: info@polisportivasanmarinese.it</p>

<h3>2. Dati raccolti e finalità del trattamento</h3>
<p>L'Associazione tratta i dati personali degli associati, atleti e contatti per le seguenti finalità:</p>
<ul>
  <li><strong>Gestione del rapporto associativo</strong> (tesseramento, iscrizioni, quote) — base giuridica: esecuzione di un contratto (art. 6 par. 1 lett. b GDPR);</li>
  <li><strong>Adempimenti di legge e fiscali</strong> — base giuridica: obbligo legale (art. 6 par. 1 lett. c GDPR);</li>
  <li><strong>Comunicazioni istituzionali e attività associative</strong> — base giuridica: legittimo interesse (art. 6 par. 1 lett. f GDPR);</li>
  <li><strong>Pubblicazione di foto e video sui canali dell'Associazione</strong> — base giuridica: consenso (art. 6 par. 1 lett. a GDPR), da raccogliere separatamente;</li>
  <li><strong>Tutela dei minori (safeguarding)</strong> — base giuridica: obbligo legale (D.lgs 39/2021) e legittimo interesse.</li>
</ul>

<h3>3. Dati particolari</h3>
<p>In relazione all'attività sportiva, l'Associazione può trattare dati relativi alla salute degli atleti (certificati medici, idoneità sportiva) esclusivamente per le finalità connesse all'iscrizione alle gare e alla sicurezza durante l'attività. Base giuridica: consenso esplicito (art. 9 par. 2 lett. a GDPR) e obblighi di legge.</p>

<h3>4. Comunicazione e diffusione dei dati</h3>
<p>I dati non saranno ceduti a terzi per finalità commerciali. Potranno essere comunicati a:</p>
<ul>
  <li>Federazioni sportive di affiliazione (FCI, UISP, ARCI) per le pratiche di tesseramento;</li>
  <li>Consulenti fiscali e legali dell'Associazione, vincolati da accordi di riservatezza;</li>
  <li>Autorità pubbliche su richiesta di legge.</li>
</ul>

<h3>5. Conservazione dei dati</h3>
<p>I dati saranno conservati per il tempo strettamente necessario agli scopi per cui sono stati raccolti, e comunque non oltre 10 anni per i documenti contabili, 5 anni per la documentazione associativa ordinaria.</p>

<h3>6. Diritti degli interessati</h3>
<p>Hai il diritto di:</p>
<ul>
  <li>Accedere ai tuoi dati personali (art. 15 GDPR);</li>
  <li>Richiederne la rettifica (art. 16) o la cancellazione (art. 17);</li>
  <li>Opporti al trattamento (art. 21) o richiederne la limitazione (art. 18);</li>
  <li>Ricevere i tuoi dati in formato portabile (art. 20);</li>
  <li>Revocare il consenso in qualsiasi momento, senza pregiudizio per la liceità del trattamento anteriore.</li>
</ul>
<p>Per esercitare i tuoi diritti, scrivi a: <strong>info@polisportivasanmarinese.it</strong></p>

<h3>7. Reclami</h3>
<p>Hai il diritto di proporre reclamo al Garante per la Protezione dei Dati Personali (www.garanteprivacy.it) se ritieni che il trattamento dei tuoi dati violi il GDPR.</p>''',
    },
]


def load_documents(apps, schema_editor):
    Document = apps.get_model('documents', 'Document')
    for data in DOCUMENTS:
        slug = slugify(data['title'])
        Document.objects.get_or_create(
            slug=slug,
            defaults={
                'title': data['title'],
                'category': data['category'],
                'order': data['order'],
                'description': data['description'],
                'content': data['content'],
                'active': True,
            }
        )


def unload_documents(apps, schema_editor):
    Document = apps.get_model('documents', 'Document')
    slugs = [slugify(d['title']) for d in DOCUMENTS]
    Document.objects.filter(slug__in=slugs).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0002_document_content_document_slug_and_more'),
    ]

    operations = [
        migrations.RunPython(load_documents, reverse_code=unload_documents),
    ]
