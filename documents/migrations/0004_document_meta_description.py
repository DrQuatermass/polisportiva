from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0003_initial_documents'),
    ]

    operations = [
        migrations.AddField(
            model_name='document',
            name='meta_description',
            field=models.CharField(
                blank=True,
                help_text='Testo mostrato da Google (max 160 caratteri). Se vuoto viene generato da descrizione/contenuto.',
                max_length=160,
                verbose_name='Meta description',
            ),
        ),
    ]
