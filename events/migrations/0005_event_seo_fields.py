from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0004_event_published'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='meta_description',
            field=models.CharField(
                blank=True,
                help_text='Testo mostrato da Google e social (max 160 caratteri). Se vuoto viene generato dalla descrizione.',
                max_length=160,
                verbose_name='Meta description',
            ),
        ),
        migrations.AddField(
            model_name='event',
            name='og_image',
            field=models.ImageField(
                blank=True,
                help_text="1200x630 consigliato. Se vuoto usa l'immagine principale.",
                null=True,
                upload_to='events/og/',
                verbose_name='Immagine social (opzionale)',
            ),
        ),
    ]
