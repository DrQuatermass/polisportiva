import shutil
import tempfile

from django.core.files.base import ContentFile
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Document


TEST_MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
@override_settings(MIDDLEWARE=[
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
])
class DocumentDownloadTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEST_MEDIA_ROOT, ignore_errors=True)

    def test_document_file_is_served_as_download(self):
        document = Document.objects.create(
            title='Regolamento',
            slug='regolamento',
            category='regolamento',
            active=True,
        )
        document.file.save('regolamento.pdf', ContentFile(b'%PDF-1.4 test'), save=True)

        response = self.client.get(reverse('document_download', kwargs={'slug': document.slug}))

        self.assertEqual(response.status_code, 200)
        self.assertIn('attachment', response['Content-Disposition'])
        self.assertIn('regolamento.pdf', response['Content-Disposition'])

    def test_inactive_document_file_is_not_downloadable(self):
        document = Document.objects.create(
            title='Documento riservato',
            slug='documento-riservato',
            category='privacy',
            active=False,
        )
        document.file.save('riservato.pdf', ContentFile(b'%PDF-1.4 test'), save=True)

        response = self.client.get(reverse('document_download', kwargs={'slug': document.slug}))

        self.assertEqual(response.status_code, 404)
