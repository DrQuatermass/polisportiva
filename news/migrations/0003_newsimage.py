from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('news', '0002_news_seo_fields'),
    ]

    operations = [
        migrations.CreateModel(
            name='NewsImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='news/gallery/', verbose_name='Foto')),
                ('caption', models.CharField(blank=True, max_length=200, verbose_name='Didascalia')),
                ('order', models.PositiveIntegerField(default=0, verbose_name='Ordine')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Data caricamento')),
                ('news', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='gallery_images', to='news.news')),
            ],
            options={
                'verbose_name': 'Foto notizia',
                'verbose_name_plural': 'Foto notizia',
                'ordering': ['order', 'id'],
            },
        ),
    ]
