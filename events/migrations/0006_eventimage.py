from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0005_event_seo_fields'),
    ]

    operations = [
        migrations.CreateModel(
            name='EventImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='events/gallery/', verbose_name='Foto')),
                ('caption', models.CharField(blank=True, max_length=200, verbose_name='Didascalia')),
                ('order', models.PositiveIntegerField(default=0, verbose_name='Ordine')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Data caricamento')),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='gallery_images', to='events.event')),
            ],
            options={
                'verbose_name': 'Foto evento',
                'verbose_name_plural': 'Foto evento',
                'ordering': ['order', 'id'],
            },
        ),
    ]
