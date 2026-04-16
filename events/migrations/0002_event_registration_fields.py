from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0001_initial'),
    ]

    operations = [
        # Nuovi campi su Event
        migrations.AddField(
            model_name='event',
            name='registration_enabled',
            field=models.BooleanField(default=False, verbose_name='Abilita iscrizioni'),
        ),
        migrations.AddField(
            model_name='event',
            name='registration_deadline',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Scadenza iscrizioni'),
        ),
        migrations.AddField(
            model_name='event',
            name='max_registrations',
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name='Posti massimi'),
        ),
        migrations.AddField(
            model_name='event',
            name='registration_price',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=8, verbose_name='Quota iscrizione (€)'),
        ),
        migrations.AddField(
            model_name='event',
            name='registration_notes',
            field=models.TextField(blank=True, verbose_name='Note per gli iscritti'),
        ),
        # RegistrationField
        migrations.CreateModel(
            name='RegistrationField',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('field_type', models.CharField(
                    choices=[
                        ('text', 'Testo breve'), ('email', 'Email'), ('phone', 'Telefono'),
                        ('textarea', 'Testo lungo'), ('select', 'Scelta singola (dropdown)'),
                        ('radio', 'Scelta singola (radio button)'), ('checkbox', 'Casella di spunta'),
                        ('file', 'Allegato (PDF / immagine)'), ('date', 'Data'), ('number', 'Numero'),
                    ],
                    max_length=20, verbose_name='Tipo campo',
                )),
                ('label', models.CharField(max_length=200, verbose_name='Etichetta')),
                ('help_text', models.CharField(blank=True, max_length=500, verbose_name='Testo di aiuto')),
                ('required', models.BooleanField(default=True, verbose_name='Obbligatorio')),
                ('order', models.PositiveIntegerField(default=0, verbose_name='Ordine')),
                ('options', models.TextField(blank=True, verbose_name='Opzioni')),
                ('event', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='fields', to='events.event',
                )),
            ],
            options={'ordering': ['order', 'id'], 'verbose_name': 'Campo iscrizione'},
        ),
        # Registration
        migrations.CreateModel(
            name='Registration',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ('email', models.EmailField(verbose_name='Email')),
                ('submitted_at', models.DateTimeField(auto_now_add=True, verbose_name='Data iscrizione')),
                ('payment_status', models.CharField(
                    choices=[
                        ('free', 'Gratuito'), ('pending', 'In attesa di pagamento'),
                        ('completed', 'Pagamento completato'), ('failed', 'Pagamento fallito'),
                        ('cancelled', 'Annullato'),
                    ],
                    default='free', max_length=20, verbose_name='Stato pagamento',
                )),
                ('paypal_order_id', models.CharField(blank=True, max_length=200)),
                ('amount_paid', models.DecimalField(decimal_places=2, default=0, max_digits=8, verbose_name='Importo pagato (€)')),
                ('event', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='registrations', to='events.event',
                )),
            ],
            options={'ordering': ['-submitted_at'], 'verbose_name': 'Iscrizione', 'verbose_name_plural': 'Iscrizioni'},
        ),
        # RegistrationAnswer
        migrations.CreateModel(
            name='RegistrationAnswer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('value', models.TextField(blank=True, verbose_name='Valore')),
                ('file', models.FileField(blank=True, null=True, upload_to='registrations/', verbose_name='File allegato')),
                ('field', models.ForeignKey(
                    null=True, on_delete=django.db.models.deletion.SET_NULL,
                    to='events.registrationfield',
                )),
                ('registration', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='answers', to='events.registration',
                )),
            ],
        ),
    ]
