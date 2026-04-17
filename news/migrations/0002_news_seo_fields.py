from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('news', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='news',
            name='meta_description',
            field=models.CharField(
                blank=True,
                help_text='Testo mostrato da Google e social (max 160 caratteri). Se vuoto viene generato dal contenuto.',
                max_length=160,
                verbose_name='Meta description',
            ),
        ),
        migrations.AddField(
            model_name='news',
            name='og_image',
            field=models.ImageField(
                blank=True,
                help_text="1200x630 consigliato. Se vuoto usa l'immagine principale.",
                null=True,
                upload_to='news/og/',
                verbose_name='Immagine social (opzionale)',
            ),
        ),
    ]
